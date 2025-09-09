import json
import os
import re
import time
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageEntityUrl
from datetime import datetime
import spacy
import sys
import asyncio  


# API ID and hash
api_id = '21046839'
api_hash = '0ecb0f1db8f5b5e342fe8f61aad8fb60'

# Phone number associated with your Telegram account
phone_number = '+966559166818'

# List of Telegram channel URLs
channel_urls = [
    "https://t.me/TheDarkWebInformer",
    "https://t.me/hackmanac",
    "https://t.me/esteemrestorationeagle",
    "https://t.me/alixsecenglish",
    "https://t.me/vxunderground",
    "https://t.me/DarkfeedNews",
    "https://t.me/Team_R70",
    "https://t.me/RansomwareNewsVX",
    "https://t.me/RansomFeedNews",
    "https://t.me/yildizthreatnews",
    "https://t.me/cyberthint",
    "https://t.me/INDOHAXSEC",
    "https://t.me/ransomlook",
    "https://t.me/RedPacketSecurity",
    "https://t.me/ransomwarelive",
    "https://t.me/Laneh_dark",
]


# Output / aux files
JSON_OUTPUT = 'NewPosts.json'
FAILED_CHANNELS_FILE = 'failed_channels.json'

# Attack keywords (category -> triggers)
detailed_attack_keywords = {
    "DDoS Attacks": ["ddos", "denial of service", "flooding", "botnet", "amplification"],
    "Hacking": ["hack", "hacked", "hacking", "exploited", "vulnerability", "rce", "breached"],
    "Defacement": ["deface", "defaced", "website defacement"],
    "Data Breach": ["breach", "data leak", "leaked data", "stolen data", "compromised data"],
    "Phishing": ["phishing", "phish", "spear phishing", "email scam"]
}

# =========================
# NLP Setup
# =========================
nlp = spacy.load("en_core_web_sm")

# =========================
# Utility Functions
# =========================

def load_existing_messages(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_messages(file_path: str, messages: dict):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

def load_keywords_from_file(file_path: str):
    """
    Load keywords from JSON list file and return a cleaned list.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            # keep original casing for output, but ensure no empties
            return [kw.strip() for kw in data if isinstance(kw, str) and kw.strip()]
        print(f"Unexpected JSON structure in {file_path}: {type(data)}")
        return []
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def extract_location(text: str):
    """
    Use spaCy (GPE) to extract locations. Returns ['N/A'] if none found.
    """
    if not text:
        return ["N/A"]
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return locations if locations else ["N/A"]

def match_keywords(text: str, keywords: list):
    """
    Return a list of matched keywords (original casing). If nothing matches, return [].
    - Tries whole-word regex first (helpful for Latin).
    - Falls back to substring match (helps Arabic / mixed scripts).
    """
    if not text or not keywords:
        return []

    norm_text = re.sub(r'[^\w\s]', ' ', text.lower())

    matches_norm = set()
    norm_to_original = {}

    for kw in keywords:
        norm_kw = kw.lower().strip()
        if not norm_kw:
            continue
        norm_to_original[norm_kw] = kw

        # Whole-word regex (works well for Latin)
        if re.search(rf'\b{re.escape(norm_kw)}\b', norm_text):
            matches_norm.add(norm_kw)
            continue

        # Fallback substring (better for Arabic/phrases)
        if norm_kw in norm_text:
            matches_norm.add(norm_kw)

    return sorted([norm_to_original[m] for m in matches_norm])

def detect_attack_type(text: str):
    if not text:
        return "Unknown"
    content_lower = text.lower()
    for category, triggers in detailed_attack_keywords.items():
        if any(t in content_lower for t in triggers):
            return category
    return "Unknown"

def extract_urls_from_message(msg):
    """
    Extract URLs from Telethon message entities (MessageEntityUrl, MessageEntityTextUrl).
    """
    urls = []
    try:
        if msg and msg.entities:
            for ent in msg.entities:
                if isinstance(ent, MessageEntityUrl):
                    urls.append(msg.message[ent.offset:ent.offset + ent.length])
                elif isinstance(ent, MessageEntityTextUrl) and getattr(ent, 'url', None):
                    urls.append(ent.url)
    except Exception:
        pass
    return urls

def log_failed_channel(channel_identifier: str, failed_channels_file: str = FAILED_CHANNELS_FILE):
    try:
        if os.path.exists(failed_channels_file):
            with open(failed_channels_file, 'r', encoding='utf-8') as f:
                failed_channels = json.load(f)
        else:
            failed_channels = []

        if channel_identifier not in failed_channels:
            failed_channels.append(channel_identifier)

        with open(failed_channels_file, 'w', encoding='utf-8') as f:
            json.dump(failed_channels, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error handling {failed_channels_file}: {e}")

# =========================
# Telegram Fetch
# =========================

client = TelegramClient('anon', api_id, api_hash)

async def fetch_messages(channel_identifier, existing_message_ids_set):
    """
    Returns: (channel_id, channel_title, [new_messages])
    """
    try:
        channel = await client.get_entity(channel_identifier)
    except Exception as e:
        print(f"Failed to fetch channel '{channel_identifier}': {e}")
        log_failed_channel(channel_identifier)
        return None, None, []

    limit = 100
    offset_id = 0

    try:
        history = await client(GetHistoryRequest(
            peer=channel,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        messages = history.messages
    except Exception as e:
        print(f"Error fetching messages for channel '{channel_identifier}': {e}")
        return channel.id, channel.title, []

    # Load both keyword lists ONCE per fetch
    company_keywords = load_keywords_from_file('Company.json')
    arabic_keywords  = load_keywords_from_file('KeyWords.json')

    new_messages = []

    for message in messages:
        if message.id in existing_message_ids_set:
            continue

        post_text = message.message or ""
        discovered_date = message.date.strftime('%Y-%m-%d') if message.date else datetime.utcnow().strftime('%Y-%m-%d')

        urls = extract_urls_from_message(message)
        attack_type = detect_attack_type(post_text)
        location = extract_location(post_text)

        # --- Keyword matching (fixed logic) ---
        company_matches = match_keywords(post_text, company_keywords)
        arabic_matches  = match_keywords(post_text, arabic_keywords)

        combined_matches = sorted(set(company_matches + arabic_matches))

        # If nothing matched -> ["Other"], else only the matches (no "Other")
        matched_keywords = combined_matches if combined_matches else ["Other"]
        # --------------------------------------

        new_messages.append({
            'Message ID': message.id,
            'discovered': discovered_date,
            'post_title': post_text if post_text else "No Text Content",
            'Attack Type': attack_type,
            'Location': location,
            'URLs': urls,
            'Matched Keywords': matched_keywords
        })

        offset_id = message.id  # (kept if you plan to paginate later)

    return channel.id, channel.title, new_messages

# =========================
# Main Loop
# =========================

async def main():
    iteration_count = 0
    max_iterations = 1   # run once by default
    channel_id_map = {}

    while True:
        all_channel_messages = load_existing_messages(JSON_OUTPUT) or {}

        await client.start(phone=phone_number)

        # Make a global set of existing IDs across all channels to skip duplicates
        global_existing_ids = {msg['Message ID']
                               for msgs in all_channel_messages.values()
                               for msg in msgs}

        for channel_url in channel_urls:
            channel_identifier = channel_id_map.get(channel_url, channel_url)

            try:
                channel_id, channel_name, new_msgs = await fetch_messages(
                    channel_identifier,
                    existing_message_ids_set=global_existing_ids
                )
            except Exception as e:
                print(f"Error processing channel {channel_url}: {e}")
                continue

            if channel_id is None or channel_name is None:
                continue

            channel_id_map[channel_url] = channel_id

            if channel_name not in all_channel_messages:
                all_channel_messages[channel_name] = []

            # De-duplicate within the channel
            existing_ids_in_channel = {m['Message ID'] for m in all_channel_messages[channel_name]}
            unique_new = [m for m in new_msgs if m['Message ID'] not in existing_ids_in_channel]

            # Update the global set to avoid re-adding across channels
            global_existing_ids.update({m['Message ID'] for m in unique_new})

            all_channel_messages[channel_name].extend(unique_new)

        save_messages(JSON_OUTPUT, all_channel_messages)

        iteration_count += 1
        print(f"Data updated. Iteration {iteration_count}.")

        await client.disconnect()

        if iteration_count >= max_iterations:
            print("Maximum iterations reached. Terminating the script.")
            return

        # If you want it to loop, keep this sleep + reconnect
        time.sleep(60)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())