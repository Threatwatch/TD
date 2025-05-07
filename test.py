# # import requests
# # import feedparser
# # import json
# # from bs4 import BeautifulSoup
# # from datetime import datetime

# # # Step 1: Scrape the RSS feed links from Feedspot
# # def scrape_rss_links():
# #     url = 'https://rss.feedspot.com/cyber_security_news_rss_feeds/'
# #     headers = {
# #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
# #     }
# #     response = requests.get(url, headers=headers)

# #     rss_links = []

# #     if response.status_code == 200:
# #         soup = BeautifulSoup(response.content, 'html.parser')
# #         for a_tag in soup.find_all('a', href=True):
# #             href = a_tag['href']
# #             if 'rss' in href or 'feed' in href:
# #                 rss_links.append(href)

# #         rss_links = list(set(rss_links))  # Remove duplicates
# #     else:
# #         print(f"Failed to scrape Feedspot. Status code: {response.status_code}")

# #     return rss_links

# # # Step 2: Fetch today's news from all RSS feeds
# # def fetch_todays_news(rss_links):
# #     today = datetime.utcnow().date()
# #     all_news = {}

# #     headers = {
# #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
# #     }

# #     for url in rss_links:
# #         try:
# #             print(f"Fetching from {url}")
# #             response = requests.get(url, headers=headers, timeout=10)
# #             if response.status_code == 200:
# #                 feed = feedparser.parse(response.content)
# #                 feed_title = feed.feed.get('title', 'Unknown Feed')
# #                 all_news[feed_title] = []

# #                 for entry in feed.entries:
# #                     if 'published_parsed' in entry:
# #                         published_date = datetime(*entry.published_parsed[:6]).date()
# #                         if published_date == today:
# #                             news_item = {
# #                                 'title': entry.title,
# #                                 'link': entry.link,
# #                                 'published': str(published_date)
# #                             }
# #                             all_news[feed_title].append(news_item)
# #             else:
# #                 print(f"Failed to fetch RSS feed: {url} (Status code {response.status_code})")

# #         except Exception as e:
# #             print(f"Error fetching {url}: {e}")

# #     return all_news

# # # Step 3: Save news into a JSON file
# # def save_news_to_json(all_news):
# #     with open('todays_news.json', 'w', encoding='utf-8') as f:
# #         json.dump(all_news, f, indent=4, ensure_ascii=False)
# #     print("Today's news saved to todays_news.json")


# # # === MAIN PROCESS ===
# # if __name__ == "__main__":
# #     rss_links = scrape_rss_links()
# #     if rss_links:
# #         all_news = fetch_todays_news(rss_links)
# #         save_news_to_json(all_news)
# #     else:
# #         print("No RSS links found.")
# import requests
# import feedparser
# import json
# from bs4 import BeautifulSoup
# from datetime import datetime, timedelta

# # Step 1: Scrape the RSS feed links from Feedspot
# def scrape_rss_links():
#     url = 'https://rss.feedspot.com/cyber_security_news_rss_feeds/'
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
#     }
#     response = requests.get(url, headers=headers)

#     rss_links = []

#     if response.status_code == 200:
#         soup = BeautifulSoup(response.content, 'html.parser')
#         for a_tag in soup.find_all('a', href=True):
#             href = a_tag['href']
#             if 'rss' in href or 'feed' in href:
#                 rss_links.append(href)

#         rss_links = list(set(rss_links))  # Remove duplicates
#     else:
#         print(f"Failed to scrape Feedspot. Status code: {response.status_code}")

#     return rss_links

# # Step 2: Fetch last 24 hours news from all RSS feeds
# def fetch_last_24h_news(rss_links):
#     now = datetime.utcnow()
#     yesterday = now - timedelta(days=1)
#     all_news = {}

#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
#     }

#     for url in rss_links:
#         try:
#             print(f"Fetching from {url}")
#             response = requests.get(url, headers=headers, timeout=10)
#             if response.status_code == 200:
#                 feed = feedparser.parse(response.content)
#                 feed_title = feed.feed.get('title', 'Unknown Feed')
#                 all_news[feed_title] = []

#                 for entry in feed.entries:
#                     if 'published_parsed' in entry:
#                         published_datetime = datetime(*entry.published_parsed[:6])
#                         if published_datetime >= yesterday:
#                             news_item = {
#                                 'title': entry.title,
#                                 'link': entry.link,
#                                 'published': str(published_datetime.date())
#                             }
#                             all_news[feed_title].append(news_item)
#             else:
#                 print(f"Failed to fetch RSS feed: {url} (Status code {response.status_code})")

#         except Exception as e:
#             print(f"Error fetching {url}: {e}")

#     return all_news

# # Step 3: Save news into a JSON file
# def save_news_to_json(all_news):
#     with open('last_24h_news.json', 'w', encoding='utf-8') as f:
#         json.dump(all_news, f, indent=4, ensure_ascii=False)
#     print("Last 24 hours' news saved to last_24h_news.json")


# # === MAIN PROCESS ===
# if __name__ == "__main__":
#     rss_links = scrape_rss_links()
#     if rss_links:
#         all_news = fetch_last_24h_news(rss_links)
#         save_news_to_json(all_news)
#     else:
#         print("No RSS links found.")
