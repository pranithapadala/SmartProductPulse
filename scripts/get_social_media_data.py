# scripts/get_social_media_data.py (Version 4: Reddit-Only)
# import tweepy # No longer needed
import praw
import pandas as pd
import os
import time
import re

# --- Section 1: Manual Config File Reader ---
config = {}
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(project_root, 'config.py')
try:
    with open(config_path, 'r') as f:
        for line in f:
            match = re.search(r"^\s*(\w+)\s*=\s*[\"'](.+?)[\"']", line)
            if match:
                key, value = match.groups()
                config[key] = value
    # Only need Reddit keys now
    required_keys = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT']
    if not all(k in config for k in required_keys):
        raise ValueError("One or more required Reddit keys are missing from config.py.")
except Exception as e:
    print(f"FATAL ERROR: Could not read or parse config.py. Error: {e}")
    exit()

print("--- Starting Social Media Scraping (Cool Gadgets Edition) ---")
print("NOTE: Due to Twitter API Free Tier restrictions, this script will now only scrape data from Reddit.")


# --- Section 2: Configuration ---
RAW_DATA_DIR = os.path.join(project_root, "data/raw")
PRODUCTS_FILE = os.path.join(RAW_DATA_DIR, "cool_gadgets_products.csv") 
# TWEETS_OUTPUT_FILE = os.path.join(RAW_DATA_DIR, "raw_tweets.csv") # No longer needed
REDDIT_OUTPUT_FILE = os.path.join(RAW_DATA_DIR, "raw_reddit_posts.csv")
MAX_POSTS_PER_PRODUCT = 100
SUBREDDITS_TO_SEARCH = ['apple', 'iphone', 'visionpro', 'samsung', 'gaminglaptops', 'playstation', 'nintendo', 'gadgets', 'technology', 'laptops']

# --- Section 3: Load Product Data ---
print("\nStep 1: Loading product list...")
try:
    products_df = pd.read_csv(PRODUCTS_FILE)
    products_df['search_term'] = products_df['title']
    product_search_terms = products_df[['id', 'search_term']]
    print(f"Loaded {len(product_search_terms)} products to search for.")
except FileNotFoundError:
    print(f"FATAL ERROR: Products file not found at '{PRODUCTS_FILE}'.")
    exit()

# --- Section 4: Scrape Twitter Data (SKIPPED) ---
# Due to the severe limitations and costs of the new Twitter API,
# this functionality has been disabled for this project.
# print("\nStep 2: Scraping Twitter... (SKIPPED)")


# --- Section 5: Scrape Reddit Data ---
print("\nStep 2: Scraping Reddit...") # Changed to Step 2
try:
    reddit = praw.Reddit(client_id=config['REDDIT_CLIENT_ID'], client_secret=config['REDDIT_CLIENT_SECRET'], user_agent=config['REDDIT_USER_AGENT'])
    print("  -> Successfully authenticated with Reddit API.")
except Exception as e:
    print(f"FATAL ERROR: Could not authenticate with Reddit. Error: {e}")
    exit()

all_reddit_posts = []
for index, row in product_search_terms.iterrows():
    product_id = row['id']
    reddit_query = f'"{row["search_term"]}"'
    print(f'  -> Searching Reddit for: {reddit_query}...')
    for subreddit_name in SUBREDDITS_TO_SEARCH:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            # We can be a bit more generous with Reddit's limit
            limit_per_sub = (MAX_POSTS_PER_PRODUCT // len(SUBREDDITS_TO_SEARCH)) + 5
            for submission in subreddit.search(reddit_query, limit=limit_per_sub, sort='new'):
                all_reddit_posts.append({
                    'product_id': product_id, 
                    'source': 'Reddit', 
                    'date': pd.to_datetime(submission.created_utc, unit='s'), 
                    'text': f"{submission.title} {submission.selftext}", 
                    'username': submission.author.name if submission.author else '[deleted]',
                    'location': None # Placeholder for consistency
                })
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ Warning: Could not scrape subreddit '{subreddit_name}'. Error: {e}")

if all_reddit_posts:
    reddit_df = pd.DataFrame(all_reddit_posts)
    reddit_df.drop_duplicates(subset=['text'], inplace=True, keep='first')
    reddit_df.to_csv(REDDIT_OUTPUT_FILE, index=False, columns=['product_id', 'source', 'date', 'text', 'username', 'location'])
    print(f"Success: Scraped a total of {len(reddit_df)} Reddit posts and saved to '{REDDIT_OUTPUT_FILE}'.")
else:
    print("No Reddit posts found for any product.")

print("\n--- Social Media Scraping Complete ---")