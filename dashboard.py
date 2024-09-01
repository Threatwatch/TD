import json
import os
import time
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageEntityUrl
from datetime import datetime
import spacy
import sys

# Your API ID and hash
api_id = '21046839'
api_hash = '0ecb0f1db8f5b5e342fe8f61aad8fb60'

# Phone number associated with your Telegram account
phone_number = '+966559166818'

# List of Telegram channel URLs
channel_urls = [
    "https://t.me/TheDarkWebInformer",
    "https://t.me/RipperSec",
]


# Create the client and connect
client = TelegramClient('anon', api_id, api_hash)

# Load spaCy model for English
nlp = spacy.load("en_core_web_sm")

def load_existing_messages(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    return {}

def save_messages(file_path, messages):
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(messages, json_file, ensure_ascii=False, indent=4)

# Define the detailed attack keywords for categorization
detailed_attack_keywords = {
    "DDoS Attacks": ["ddos", "denial of service", "flooding", "botnet", "amplification"],
    "Hacking": ["hack", "hacked", "hacking", "exploited", "vulnerability", "rce", "breached"],
    "Defacement": ["deface", "defaced", "website defacement"],
    "Data Breach": ["breach", "data leak", "leaked data", "stolen data", "compromised data"],
    "Phishing": ["phishing", "phish", "spear phishing", "email scam"]
}

def extract_location(text):
    # Use spaCy to detect locations (GPE: Geopolitical Entity)
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return locations if locations else ["N/A"]

async def fetch_messages(channel_identifier, existing_messages_ids):
    try:
        channel = await client.get_entity(channel_identifier)
    except Exception as e:
        print(f"Failed to fetch the channel {channel_identifier}: {e}")
        return None, None, []

    limit = 100
    offset_id = 0
    new_messages = []

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

    for message in messages:
        if message.id not in existing_messages_ids:
            date = message.date.strftime('%Y-%m-%d')
            
            # Extract URLs if available
            urls = []
            if message.entities:
                for entity in message.entities:
                    if isinstance(entity, MessageEntityUrl):
                        urls.append(message.message[entity.offset:entity.offset + entity.length])

            # Determine the attack type based on content
            attack_type = "Unknown"
            if message.message:
                content_lower = message.message.lower()
                for category, keywords in detailed_attack_keywords.items():
                    if any(keyword in content_lower for keyword in keywords):
                        attack_type = category
                        break

            # Extract location from the message content
            location = extract_location(message.message) if message.message else ["N/A"]
            
            new_messages.append({
                'Message ID': message.id,
                'Date': date,
                'Content': message.message,
                'Attack Type': attack_type,
                'Location': location,
                'URLs': urls
            })
        offset_id = message.id

    return channel.id, channel.title, new_messages

async def main():
    json_file_path = 'posts.json'
    iteration_count = 0
    max_iterations = 1
    channel_id_map = {}  # Dictionary to store channel URL to ID mappings

    while True:
        all_channel_messages = load_existing_messages(json_file_path)
        if not all_channel_messages:
            all_channel_messages = {}

        await client.start(phone=phone_number)

        for channel_url in channel_urls:
            channel_identifier = channel_id_map.get(channel_url, channel_url)
            channel_id, channel_name, new_messages = await fetch_messages(channel_identifier, 
                {msg['Message ID'] for channel in all_channel_messages.values() for msg in channel})
            if channel_id:
                channel_id_map[channel_url] = channel_id
            if channel_name not in all_channel_messages:
                all_channel_messages[channel_name] = []
            
            # Add only new messages that are not already in the list
            existing_message_ids = {msg['Message ID'] for msg in all_channel_messages[channel_name]}
            unique_new_messages = [msg for msg in new_messages if msg['Message ID'] not in existing_message_ids]
            all_channel_messages[channel_name].extend(unique_new_messages)

        save_messages(json_file_path, all_channel_messages)

        iteration_count += 1
        print(f"Data updated. Iteration {iteration_count}. Sleeping for 1 minute.")

        if iteration_count >= max_iterations:
            print("Maximum iterations reached. Terminating the script.")
            await client.disconnect()
            sys.exit()

        await client.disconnect()
        time.sleep(60)

with client:
    client.loop.run_until_complete(main())
