import json
import os
import subprocess
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
    'https://t.me/LulzsecMuslims_World',
    'https://t.me/Anonymous_KSA',
    'https://t.me/testForapi174'
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
    print(f"Saving messages to {file_path}")
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(messages, json_file, ensure_ascii=False, indent=4)

# Define the detailed attack keywords for categorization based on VERIS framework
detailed_attack_keywords = {
    "DoS (Denial of Service)": ["ddos", "denial of service", "flooding", "botnet", "amplification"],
    "Hacking": ["hack", "hacked", "hacking", "exploit", "exploited", "vulnerability", "rce", "breach", "breached", "unauthorized access"],
    "Malware": ["malware", "ransomware", "virus", "worm", "trojan", "spyware", "adware", "keylogger"],
    "Social Engineering": ["phishing", "phish", "spear phishing", "email scam", "social engineering", "vishing", "pretexting"],
    "Misuse": ["abuse", "misuse", "privilege abuse", "unauthorized use"],
    "Defacement": ["deface", "defaced", "website defacement", "graffiti"],
    "Data Breach": ["data breach", "data leak", "leaked data", "stolen data", "compromised data", "exfiltration", "data theft"],
}

def extract_location(text):
    # Use spaCy to detect locations (GPE: Geopolitical Entity)
    doc = nlp(text)
    locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    # Filter out URLs mistakenly recognized as locations
    locations = [loc for loc in locations if not loc.startswith('http')]
    return locations if locations else ["N/A"]

async def fetch_messages(channel_url, existing_messages_ids):
    channel = await client.get_entity(channel_url)
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
            # Extract date without time
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

    return channel.username if channel.username else 'N/A', new_messages

def commit_and_push_changes(file_path):
    try:
        # Initialize git repository if not already done
        if not os.path.exists('.git'):
            subprocess.run(["git", "init"], check=True)

        # Ensure we are on the main branch
        subprocess.run(["git", "checkout", "-B", "main"], check=True)

        # Add the specific file to the staging area
        subprocess.run(["git", "add", file_path], check=True)

        # Check if there are changes to commit
        result = subprocess.run(["git", "status", "--porcelain"], stdout=subprocess.PIPE)
        if result.stdout:
            # Commit the changes
            subprocess.run(["git", "commit", "-m", "Update JSON data"], check=True)

            # Push the changes to the main branch
            subprocess.run(["git", "push", "origin", "main"], check=True)
        else:
            print("No changes to commit.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while pushing changes: {e}")

async def main():
    json_file_path = 'new_messages.json'  # Path to save the JSON file
    iteration_count = 0
    max_iterations = 1  # Set the maximum number of iterations

    while True:
        all_channel_messages = load_existing_messages(json_file_path)
        if not all_channel_messages:
            all_channel_messages = {}

        await client.start(phone=phone_number)

        for channel_url in channel_urls:
            print(f"Fetching messages from {channel_url}")
            channel_name, new_messages = await fetch_messages(channel_url, 
                {msg['Message ID'] for channel in all_channel_messages.values() for msg in channel})
            if channel_name not in all_channel_messages:
                all_channel_messages[channel_name] = []
            # Prepend new messages to the list
            all_channel_messages[channel_name] = new_messages + all_channel_messages[channel_name]

        save_messages(json_file_path, all_channel_messages)

        # Commit and push changes to the repository
        commit_and_push_changes(json_file_path)

        iteration_count += 1
        print(f"Data updated. Iteration {iteration_count}. Sleeping for 1 minute.")

        # Terminate condition
        if iteration_count >= max_iterations:
            print("Maximum iterations reached. Terminating the script.")
            await client.disconnect()
            sys.exit()

        await client.disconnect()
        time.sleep(60)

with client:
    client.loop.run_until_complete(main())
