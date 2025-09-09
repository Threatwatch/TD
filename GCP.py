import os
import re
import json
import asyncio
import tempfile
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageEntityUrl
from google.cloud import storage
from cloudevents.http import CloudEvent
import functions_framework

# === ENV VARS ===
try:
    api_id = int(os.environ["API_ID"])
    api_hash = os.environ["API_HASH"]
    bucket_name = "telegram-scraper-data"
except Exception as e:
    print(f"❌ Error loading environment variables: {e}")
    raise

# === GCS Files ===
session_blob = "cloudrun_session.session"
company_keywords_blob = "Company.json"
arabic_keywords_blob = "KeyWords.json"
failed_channels_blob = "failed_channels.json"
output_blob = "NewPosts.json"

# === Telegram Channels ===
channel_urls = [
    "https://t.me/TheDarkWebInformer", "https://t.me/hackmanac",
    "https://t.me/esteemrestorationeagle", "https://t.me/alixsecenglish",
    "https://t.me/vxunderground", "https://t.me/DarkfeedNews",
    "https://t.me/TigerElectronicUnit", "https://t.me/Team_R70",
    "https://t.me/RansomwareNewsVX", "https://t.me/RansomFeedNews",
    "https://t.me/yildizthreatnews", "https://t.me/cyberthint",
    "https://t.me/INDOHAXSEC", "https://t.me/ransomlook",
    "https://t.me/RedPacketSecurity", "https://t.me/ransomwarelive",
    "https://t.me/Laneh_dark",
]

# === Attack Categories ===
detailed_attack_keywords = {
    "DDoS Attacks": ["ddos", "denial of service", "flooding", "botnet", "amplification"],
    "Hacking": ["hack", "hacked", "hacking", "exploited", "vulnerability", "rce", "breached"],
    "Defacement": ["deface", "defaced", "website defacement"],
    "Data Breach": ["breach", "data leak", "leaked data", "stolen data", "compromised data"],
    "Phishing": ["phishing", "phish", "spear phishing", "email scam"]
}

# === GCS Helpers ===
def download_blob(blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    path = os.path.join(tempfile.gettempdir(), blob_name)
    blob.download_to_filename(path)
    return path

def read_blob_json(blob_name):
    storage_client = storage.Client()
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    return json.loads(blob.download_as_text())

def write_blob_json(blob_name, data):
    storage_client = storage.Client()
    blob = storage_client.bucket(bucket_name).blob(blob_name)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=4), content_type="application/json")

# === Keyword Matching ===
def match_keywords(text, keywords):
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    matches = set()
    original_map = {kw.lower(): kw for kw in keywords}
    for keyword in keywords:
        if re.search(rf'\b{re.escape(keyword.lower())}\b', text):
            matches.add(keyword.lower())
    return sorted([original_map[m] for m in matches]) if matches else ["Other"]

# === Failed Channels Log ===
def log_failed_channel(identifier):
    try:
        path = download_blob(failed_channels_blob)
        with open(path, 'r') as f:
            failed = json.load(f)
    except:
        failed = []
    if identifier not in failed:
        failed.append(identifier)
        write_blob_json(failed_channels_blob, failed)

# === Scrape Function ===
async def fetch_messages(client, url, company_keywords, arabic_keywords):
    try:
        channel = await client.get_entity(url)
        history = await client(GetHistoryRequest(peer=channel, offset_id=0, offset_date=None, add_offset=0, limit=50, max_id=0, min_id=0, hash=0))
        messages = history.messages
    except Exception as e:
        log_failed_channel(url)
        print(f"⚠️ Error fetching {url}: {e}")
        return []

    results = []
    for msg in messages:
        if not msg.message:
            continue
        content = msg.message
        urls = []
        if msg.entities:
            for entity in msg.entities:
                if isinstance(entity, MessageEntityUrl):
                    urls.append(content[entity.offset:entity.offset + entity.length])

        attack_type = "Unknown"
        lower = content.lower()
        for category, keys in detailed_attack_keywords.items():
            if any(k in lower for k in keys):
                attack_type = category
                break

        companies = match_keywords(content, company_keywords)
        arabics = match_keywords(content, arabic_keywords)
        all_matches = sorted(set(companies + arabics))

        results.append({
            "Message ID": msg.id,
            "discovered": msg.date.strftime('%Y-%m-%d'),
            "post_title": content,
            "Attack Type": attack_type,
            "Location": ["N/A"],
            "URLs": urls,
            "Matched Keywords": all_matches or ["Other"]
        })
    return results

# === Cloud Run Entry Point ===
@functions_framework.cloud_event
def hello_pubsub(event: CloudEvent):
    try:
        asyncio.run(scrape())
        print("✅ Scraping complete")
        return "✅ Scraping complete"
    except Exception as e:
        print(f"❌ Error in hello_pubsub: {e}")
        return f"❌ Failed: {e}"

# === Scraper Orchestration ===
async def scrape():
    try:
        session_path = download_blob(session_blob)
        company_keywords = read_blob_json(company_keywords_blob)
        arabic_keywords = read_blob_json(arabic_keywords_blob)
        all_results = []

        async with TelegramClient(session_path, api_id, api_hash) as client:
            for url in channel_urls:
                messages = await fetch_messages(client, url, company_keywords, arabic_keywords)
                all_results.extend(messages)

        write_blob_json(output_blob, all_results)
        print(f"✅ Saved {len(all_results)} messages to {output_blob}")
    except Exception as e:
        print(f"❌ Error in scrape(): {e}")
        raise
