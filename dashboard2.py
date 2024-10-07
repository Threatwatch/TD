import json
import os
import time
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import MessageEntityUrl
from datetime import datetime
import spacy
import sys
import re

# Your API ID and hash
api_id = '21046839'
api_hash = '0ecb0f1db8f5b5e342fe8f61aad8fb60'

# Phone number associated with your Telegram account
phone_number = '+966559166818'

# Channel URLs and associated groups
channel_parsing_rules = {
    "https://t.me/RansomwareNewsVX": "group_1",
    "https://t.me/RansomFeedNews": "group_2",
    "https://t.me/yildizthreatnews": "group_3",
    "https://t.me/cyberthint": "group_4"
}

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

# Extract field with regex
def extract_field(pattern, text):
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return "N/A"

def extract_urls(text):
    # Modified pattern to capture URLs without http/https or www
    # The regex will match typical domain formats followed by paths and query strings
    url_pattern = r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)"
    return re.findall(url_pattern, text)  # Returns all matches as a list


# Group-specific parsing logic
def parse_group_1(content, message_id):
    return {
        'Message ID': message_id,
        'Group': extract_field(r"Group:\s*(.*)", content),
        'Approx. Time': extract_field(r"Approx\. Time:\s*(.*)", content),
        'Title': extract_field(r"Title:\s*(.*)", content)
    }

def parse_group_2(content, message_id):
    return {
        'Message ID': message_id,
        'ID': extract_field(r"ID:\s*(\d+)", content),
        'Date': extract_field(r"⚠\s*(.*UTC)", content),
        'Ransomware Group': extract_field(r"🥷\s*(\w+)", content),
        'Victim': extract_field(r"🎯\s*(.*)", content),
        'URLs': extract_urls(content)  # Extract all URLs, regardless of the emoji
    }

def parse_group_3(content, message_id):
    return {
        'Message ID': message_id,
        'Victim': extract_field(r"Victim:\s*(.*)", content),
        'Attacker': extract_field(r"Attacker:\s*(.*)", content),
        'Disclosure Date': extract_field(r"Disclosure Date:\s*(.*)", content),
        'Leak Data Information': extract_field(r"Leak Data Information:\s*(.*)", content)
    }

def parse_group_4(content, message_id):
    # Check if it's a "Data dump" style message by looking for the "Title" field
    if "Title:" in content:
        return {
            'Message ID': message_id,
            'Title': extract_field(r"Title:\s*(.*)", content),
            'Date': extract_field(r"Date:\s*(.*)", content),
            'Source': extract_field(r"Source:\s*(https?://[^\s]+)", content)
        }
    
    # Check if it's a CVE-related message by looking for the "CVE-ID" field
    elif "CVE-ID:" in content:
        return {
            'Message ID': message_id,
            'CVE-ID': extract_field(r"CVE-ID:\s*(.*)", content),
            'Source': extract_field(r"Source:\s*(https?://[^\s]+)", content),
            'Description': extract_field(r"Description:\s*(.*)", content),
            'Publication Date': extract_field(r"Publication Date:\s*(.*)", content)
        }

    # If neither structure matches, return None (optional)
    return None

# Determine the parsing logic based on the channel URL
def parse_message(channel_url, content, message_id):
    if channel_parsing_rules.get(channel_url) == "group_1":
        return parse_group_1(content, message_id)
    elif channel_parsing_rules.get(channel_url) == "group_2":
        return parse_group_2(content, message_id)
    elif channel_parsing_rules.get(channel_url) == "group_3":
        return parse_group_3(content, message_id)
    elif channel_parsing_rules.get(channel_url) == "group_4":
        return parse_group_4(content, message_id)
    else:
        return None

# Filter messages by current month and year
def filter_messages_by_month(messages):
    current_year = datetime.now().year
    current_month = datetime.now().month

    filtered_messages = [
        msg for msg in messages
        if 'Date' in msg and datetime.strptime(msg['Date'], '%Y-%m-%d').year == current_year
        and datetime.strptime(msg['Date'], '%Y-%m-%d').month == current_month
    ]
    return filtered_messages

async def fetch_messages(channel_identifier, channel_url, existing_messages_ids):
    try:
        channel = await client.get_entity(channel_identifier)
    except Exception as e:
        print(f"Failed to fetch the channel {channel_identifier}")
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

            content = message.message if message.message else ""
            parsed_message = parse_message(channel_url, content, message.id)

            if parsed_message:
                parsed_message['Date'] = date  # Common date field
                # parsed_message['Channel Name'] = channel.title  # Add channel name to message
                new_messages.append(parsed_message)

        offset_id = message.id

    return channel.id, channel.title, new_messages

async def main():
    json_file_path = 'news.json'  # New file name for saving data
    iteration_count = 0
    max_iterations = 1
    channel_id_map = {}

    while True:
        all_news = load_existing_messages(json_file_path)
        if not all_news:
            all_news = {}

        # Filter messages for each channel
        for channel in all_news:
            all_news[channel] = filter_messages_by_month(all_news[channel])

        await client.start(phone=phone_number)

        for channel_url in channel_parsing_rules:
            channel_identifier = channel_id_map.get(channel_url, channel_url)

            # Fetch channel data and messages
            channel_id, channel_name, new_messages = await fetch_messages(channel_identifier, channel_url, 
                {msg['Message ID'] for msg in all_news.get(channel_url, []) if 'Message ID' in msg})

            if channel_id is None or channel_name is None:
                continue

            channel_id_map[channel_url] = channel_id

            # Append new messages under the appropriate channel
            if channel_name not in all_news:
                all_news[channel_name] = []

            all_news[channel_name].extend(new_messages)

        # Save filtered and new messages back to the file
        save_messages(json_file_path, all_news)

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
