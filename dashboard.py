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


# Your API ID and hash
api_id = '21046839'
api_hash = '0ecb0f1db8f5b5e342fe8f61aad8fb60'

# Phone number associated with your Telegram account
phone_number = '+966559166818'

# List of Telegram channel URLs
channel_urls = [
    "https://t.me/TheDarkWebInformer",
    "https://t.me/RipperSec",
    "https://t.me/YourAnonTl3xChatGroup",
    "https://t.me/SylhetGangSgOfficial",
    "https://t.me/hackmanac",
    "https://t.me/ANONSTU",
    "https://t.me/esteemrestorationeagle",
    "https://t.me/ServerKillers",
    "https://t.me/alixsecenglish",
    "https://t.me/vxunderground",
    "https://t.me/DarkfeedNews",
    # "https://t.me/Hunt3rkill3rs1",
    "https://t.me/TigerElectronicUnit",
    "https://t.me/CyberVolk_K",
    "https://t.me/Team_R70",
    "https://t.me/Arab_Hackers_Union",
    "https://t.me/CyberS102",
    "https://t.me/RansomwareNewsVX",
    "https://t.me/RansomFeedNews",
    "https://t.me/yildizthreatnews",
    "https://t.me/cyberthint",
    "https://t.me/GhostClanInt",
    "https://t.me/INDOHAXSEC",
    "https://t.me/ransomlook",
    "https://t.me/RedPacketSecurity",
    "https://t.me/ransomwarelive",
    # "https://t.me/AnonymousEgypt"

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

def load_keywords_from_company(file_path):
    """
    Load keywords from a JSON file and normalize them.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        list: A list of normalized keywords.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if isinstance(data, list):
                return [kw.strip() for kw in data]  # Remove any extra spaces
            else:
                print(f"Unexpected structure in {file_path}: {type(data)}")
                return []
    except Exception as e:
        print(f"Error loading keywords from {file_path}: {e}")
        return []

def match_keywords(text, keywords):
    """
    Match keywords in the text. If no match is found, return the word 'Other'.

    Args:
        text (str): The text to search.
        keywords (list): A list of keywords to match.

    Returns:
        list: A deduplicated list of matched keywords, or ['Other'] if no match is found.
    """
    text = re.sub(r'[^\w\s]', ' ', text.lower())  # Normalize text: remove special characters and convert to lowercase
    matches = set()  # Use a set to ensure no duplicates
    original_keyword_map = {}  # Map normalized keywords to their original form

    for keyword in keywords:
        normalized_keyword = keyword.lower().strip()  # Normalize the keyword
        original_keyword_map[normalized_keyword] = keyword  # Map normalized to original
        # Match as a whole word
        if re.search(rf'\b{re.escape(normalized_keyword)}\b', text):
            matches.add(normalized_keyword)  # Add normalized keyword to the matches

    # Convert matches back to their original formatting
    matched_keywords = sorted([original_keyword_map[match] for match in matches])

    # Return 'Other' if no matches found
    return matched_keywords if matched_keywords else ["Other"]

async def fetch_messages(channel_identifier, existing_messages_ids, failed_channels_file="failed_channels.json"):
    try:
        # Fetch the channel entity
        channel = await client.get_entity(channel_identifier)
    except Exception as e:
        print(f"Failed to fetch channel '{channel_identifier}': {e}")
        log_failed_channel(channel_identifier, failed_channels_file)
        return None, None, []

    # Initialize variables
    limit = 100
    offset_id = 0
    new_messages = []

    try:
        # Fetch the channel message history
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

    # Load keywords from company.json
    try:
        keywords = load_keywords_from_company('Company.json')
    except Exception as e:
        print(f"Error loading keywords: {e}")
        keywords = []

    # Process each message
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
            if message.message:  # Check if message content is not None
                content_lower = message.message.lower()
                for category, keywords_list in detailed_attack_keywords.items():
                    if any(keyword in content_lower for keyword in keywords_list):
                        attack_type = category
                        break

            # Extract location from the message content
            location = extract_location(message.message) if message.message else ["N/A"]

            # Match keywords from company.json
            matched_keywords = match_keywords(message.message or "", keywords)

            # If no keywords matched, add 'Other'
            if not matched_keywords:
                matched_keywords = ["Other"]

            # Add the processed message to the list
            new_messages.append({
                'Message ID': message.id,
                'discovered': date,
                'post_title': message.message or "No Text Content",  # Handle None message
                'Attack Type': attack_type,
                'Location': location,
                'URLs': urls,
                'Matched Keywords': matched_keywords  # Save matched keywords
            })

        # Update the offset ID to continue fetching later messages
        offset_id = message.id

    return channel.id, channel.title, new_messages

def log_failed_channel(channel_identifier, failed_channels_file):
    try:
        # Load the existing failed channels file if it exists
        if os.path.exists(failed_channels_file):
            with open(failed_channels_file, 'r') as file:
                failed_channels = json.load(file)
        else:
            failed_channels = []

        # Append the new failed channel identifier if not already logged
        if channel_identifier not in failed_channels:
            failed_channels.append(channel_identifier)
            print(f"Logging failed channel: {channel_identifier}")  # Debug print

        # Write back to the JSON file
        with open(failed_channels_file, 'w') as file:
            json.dump(failed_channels, file, indent=4)
            print(f"Failed channels updated in {failed_channels_file}")  # Debug print

    except Exception as e:
        print(f"Error handling {failed_channels_file}: {e}")

def test_match_keywords():
    """
    Test the match_keywords function with various cases.
    """
    # Sample JSON file path (adjust to your actual file path)
    json_file_path = "Company.json"

    # Load keywords from JSON file
    keywords = load_keywords_from_company(json_file_path)

    # Test cases
    test_cases = [
        {
            "text": "The company SABIC announced a new petrochemical project in Saudi Arabia.",
            "keywords": keywords,
            "expected": ['Petrochemical', 'SABIC', 'Saudi']
        },
        {
            "text": "This text has no matching keywords.",
            "keywords": keywords,
            "expected": ['Other']
        },
        {
            "text": "Completely irrelevant text.",
            "keywords": [],
            "expected": ['Other']
        }
    ]

    for i, case in enumerate(test_cases, 1):
        result = match_keywords(case["text"], case["keywords"])
        print(f"Test Case {i}: {'PASS' if result == case['expected'] else 'FAIL'}")
        print(f"  Expected: {case['expected']}\n  Got: {result}\n")

# Run the test function
if __name__ == "__main__":
    test_match_keywords()

async def main():
    json_file_path = 'NewPosts.json'
    failed_channels_file = 'failed_channels.json'
    iteration_count = 0
    max_iterations = 1
    channel_id_map = {}  # Dictionary to store channel URL to ID mappings
    
    # Test keyword matching
    test_match_keywords()

    while True:
        all_channel_messages = load_existing_messages(json_file_path)
        if not all_channel_messages:
            all_channel_messages = {}

        await client.start(phone=phone_number)

        for channel_url in channel_urls:
            channel_identifier = channel_id_map.get(channel_url, channel_url)
            try:
                channel_id, channel_name, new_messages = await fetch_messages(
                    channel_identifier, 
                    {msg['Message ID'] for channel in all_channel_messages.values() for msg in channel},
                    failed_channels_file=failed_channels_file
                )
            except Exception as e:
                print(f"Error processing channel {channel_url}: {e}")
                continue

            # Skip channels that couldn't be fetched
            if channel_id is None or channel_name is None:
                continue

            # Update channel ID map if the channel was fetched successfully
            channel_id_map[channel_url] = channel_id
            
            # Add the channel name only if valid and not already in the messages
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
            return

        await client.disconnect()
        time.sleep(60)

with client:
    client.loop.run_until_complete(main())


# import json
# import os
# import time
# from telethon.sync import TelegramClient
# from telethon.tl.functions.messages import GetHistoryRequest
# from telethon.tl.types import MessageEntityUrl
# from datetime import datetime
# import spacy
# import sys
# import asyncio  


# # Your API ID and hash
# api_id = '21046839'
# api_hash = '0ecb0f1db8f5b5e342fe8f61aad8fb60'

# # Phone number associated with your Telegram account
# phone_number = '+966559166818'

# # List of Telegram channel URLs
# channel_urls = [
#     "https://t.me/TheDarkWebInformer",
#     "https://t.me/RipperSec",
#     "https://t.me/YourAnonTl3xChatGroup",
#     "https://t.me/SylhetGangSgOfficial",
#     "https://t.me/hackmanac",
#     "https://t.me/ANONSTU",
#     "https://t.me/esteemrestorationeagle",
#     "https://t.me/ServerKillers",
#     "https://t.me/alixsecenglish",
#     "https://t.me/vxunderground",
#     "https://t.me/DarkfeedNews",
#     # "https://t.me/Hunt3rkill3rs1",
#     "https://t.me/TigerElectronicUnit",
#     "https://t.me/CyberVolk_K",
#     "https://t.me/Team_R70",
#     "https://t.me/Arab_Hackers_Union",
#     "https://t.me/CyberS102",
#     "https://t.me/RansomwareNewsVX",
#     "https://t.me/RansomFeedNews",
#     "https://t.me/yildizthreatnews",
#     "https://t.me/cyberthint",
#     "https://t.me/GhostClanInt",
#     "https://t.me/INDOHAXSEC",
#     "https://t.me/ransomlook",
#     "https://t.me/RedPacketSecurity",
#     "https://t.me/ransomwarelive",
#     # "https://t.me/AnonymousEgypt"

# ]


# # Create the client and connect
# client = TelegramClient('anon', api_id, api_hash)

# # Load spaCy model for English
# nlp = spacy.load("en_core_web_sm")

# def load_existing_messages(file_path):
#     if os.path.exists(file_path):
#         with open(file_path, 'r', encoding='utf-8') as json_file:
#             return json.load(json_file)
#     return {}

# def save_messages(file_path, messages):
#     with open(file_path, 'w', encoding='utf-8') as json_file:
#         json.dump(messages, json_file, ensure_ascii=False, indent=4)

# # Define the detailed attack keywords for categorization
# detailed_attack_keywords = {
#     "DDoS Attacks": ["ddos", "denial of service", "flooding", "botnet", "amplification"],
#     "Hacking": ["hack", "hacked", "hacking", "exploited", "vulnerability", "rce", "breached"],
#     "Defacement": ["deface", "defaced", "website defacement"],
#     "Data Breach": ["breach", "data leak", "leaked data", "stolen data", "compromised data"],
#     "Phishing": ["phishing", "phish", "spear phishing", "email scam"]
# }

# def extract_location(text):
#     # Use spaCy to detect locations (GPE: Geopolitical Entity)
#     doc = nlp(text)
#     locations = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
#     return locations if locations else ["N/A"]

# async def fetch_messages(channel_identifier, existing_messages_ids, failed_channels_file="failed_channels.json"):
#     try:
#         channel = await client.get_entity(channel_identifier)
#     except Exception as e:
#         print(f"Failed to fetch the channel {channel_identifier}: Update the URL for this channel")
#         # Log the failed channel
#         log_failed_channel(channel_identifier, failed_channels_file)
#         # Return just an empty list of messages if fetching the channel failed
#         return None, None, []

#     limit = 100
#     offset_id = 0
#     new_messages = []

#     history = await client(GetHistoryRequest(
#         peer=channel,
#         offset_id=offset_id,
#         offset_date=None,
#         add_offset=0,
#         limit=limit,
#         max_id=0,
#         min_id=0,
#         hash=0
#     ))
#     messages = history.messages

#     for message in messages:
#         if message.id not in existing_messages_ids:
#             date = message.date.strftime('%Y-%m-%d')

#             # Extract URLs if available
#             urls = []
#             if message.entities:
#                 for entity in message.entities:
#                     if isinstance(entity, MessageEntityUrl):
#                         urls.append(message.message[entity.offset:entity.offset + entity.length])

#             # Determine the attack type based on content
#             attack_type = "Unknown"
#             if message.message:
#                 content_lower = message.message.lower()
#                 for category, keywords in detailed_attack_keywords.items():
#                     if any(keyword in content_lower for keyword in keywords):
#                         attack_type = category
#                         break

#             # Extract location from the message content
#             location = extract_location(message.message) if message.message else ["N/A"]
            
#             new_messages.append({
#                 'Message ID': message.id,
#                 'discovered': date,
#                 'post_title': message.message,
#                 'Attack Type': attack_type,
#                 'Location': location,
#                 'URLs': urls
#             })
#         offset_id = message.id

#     return channel.id, channel.title, new_messages


# def log_failed_channel(channel_identifier, failed_channels_file):
#     try:
#         # Load the existing failed channels file if it exists
#         if os.path.exists(failed_channels_file):
#             with open(failed_channels_file, 'r') as file:
#                 failed_channels = json.load(file)
#         else:
#             failed_channels = []

#         # Append the new failed channel identifier if not already logged
#         if channel_identifier not in failed_channels:
#             failed_channels.append(channel_identifier)
#             print(f"Logging failed channel: {channel_identifier}")  # Debug print

#         # Write back to the JSON file
#         with open(failed_channels_file, 'w') as file:
#             json.dump(failed_channels, file, indent=4)
#             print(f"Failed channels updated in {failed_channels_file}")  # Debug print

#     except Exception as e:
#         print(f"Error handling {failed_channels_file}: {e}")

# async def main():
#     json_file_path = 'Nposts.json'
#     failed_channels_file = 'failed_channels.json'
#     iteration_count = 0
#     max_iterations = 1
#     channel_id_map = {}  # Dictionary to store channel URL to ID mappings

#     while True:
#         all_channel_messages = load_existing_messages(json_file_path)
#         if not all_channel_messages:
#             all_channel_messages = {}

#         await client.start(phone=phone_number)

#         for channel_url in channel_urls:
#             channel_identifier = channel_id_map.get(channel_url, channel_url)
#             try:
#                 channel_id, channel_name, new_messages = await fetch_messages(
#                     channel_identifier, 
#                     {msg['Message ID'] for channel in all_channel_messages.values() for msg in channel},
#                     failed_channels_file=failed_channels_file
#                 )
#             except Exception as e:
#                 print(f"Error processing channel {channel_url}: {e}")
#                 continue

#             # Skip channels that couldn't be fetched
#             if channel_id is None or channel_name is None:
#                 continue

#             # Update channel ID map if the channel was fetched successfully
#             channel_id_map[channel_url] = channel_id
            
#             # Add the channel name only if valid and not already in the messages
#             if channel_name not in all_channel_messages:
#                 all_channel_messages[channel_name] = []
            
#             # Add only new messages that are not already in the list
#             existing_message_ids = {msg['Message ID'] for msg in all_channel_messages[channel_name]}
#             unique_new_messages = [msg for msg in new_messages if msg['Message ID'] not in existing_message_ids]
#             all_channel_messages[channel_name].extend(unique_new_messages)

#         save_messages(json_file_path, all_channel_messages)

#         iteration_count += 1
#         print(f"Data updated. Iteration {iteration_count}. Sleeping for 1 minute.")

#         if iteration_count >= max_iterations:
#             print("Maximum iterations reached. Terminating the script.")
#             await client.disconnect()
#             return

#         await client.disconnect()
#         time.sleep(60)

# with client:
#     client.loop.run_until_complete(main())