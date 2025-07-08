# scripts/get_social_media_data.py
# --- Key Libraries ---
import tweepy 
import praw
import pandas as pd
import os
import time
import re

# --- Section 1: Manual Config File Reader (The fix for the file lock) ---
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
    # UPDATED: Add check for Twitter Bearer Token
    required_keys = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT', 'TWITTER_BEARER_TOKEN']
    if not all(k in config for k in required_keys):
        raise ValueError("One or more required keys are missing from config.py. Make sure REDDIT_* and TWITTER_BEARER_TOKEN are set.")
except Exception as e:
    print(f"FATAL ERROR: Could not read or parse config.py. Error: {e}")
    exit()

print("--- Starting Social Media Scraping (Cool Gadgets Edition) ---")

# --- Section 2: Configuration ---
RAW_DATA_DIR = os.path.join(project_root, "data/raw")
PRODUCTS_FILE = os.path.join(RAW_DATA_DIR, "cool_gadgets_products.csv") 
TWEETS_OUTPUT_FILE = os.path.join(RAW_DATA_DIR, "raw_tweets.csv")
REDDIT_OUTPUT_FILE = os.path.join(RAW_DATA_DIR, "raw_reddit_posts.csv")

MAX_TWEETS_PER_PRODUCT = 100
MAX_POSTS_PER_PRODUCT = 100
SUBREDDITS_TO_SEARCH = ['apple', 'iphone', 'visionpro', 'samsung', 'gaminglaptops', 'playstation', 'nintendo', 'gadgets', 'technology']


# --- Section 3: Load Product Data ---
print("\nStep 1: Loading product list...")
try:
    products_df = pd.read_csv(PRODUCTS_FILE)
    products_df['search_term'] = products_df['title']
    product_search_terms = products_df[['id', 'search_term']]
    print(f"Loaded {len(product_search_terms)} products to search for.")
except FileNotFoundError:
    print(f"FATAL ERROR: Products file not found at '{PRODUCTS_FILE}'.")
    print("Please run 'scripts/create_product_list.py' first.")
    exit()

# --- Section 4: Scrape Twitter Data (Using Tweepy and Twitter API v2) ---
# This entire section has been replaced to use Tweepy instead of snscrape.
print("\nStep 2: Scraping Twitter...")

try:
    # Initialize Tweepy client with your Bearer Token
    tweepy_client = tweepy.Client(bearer_token=config['TWITTER_BEARER_TOKEN'], wait_on_rate_limit=True)
    print("  -> Successfully authenticated with Twitter API.")
except Exception as e:
    print(f"FATAL ERROR: Could not authenticate with Twitter API. Error: {e}")
    exit()

all_tweets = []
for index, row in product_search_terms.iterrows():
    product_id = row['id']
    # Build the query for the Twitter API v2
    # -is:retweet excludes retweets, which are usually just noise.
    # lang:en ensures we only get English tweets.
    query = f'"{row["search_term"]}" -is:retweet lang:en'
    print(f'  -> Searching Twitter for: {query}...')
    
    try:
        # Use the search_recent_tweets method.
        # NOTE: The standard free API access only allows searching tweets from the last 7 days.
        # To get the username, we need to ask for it via 'expansions' and 'user.fields'.
        response = tweepy_client.search_recent_tweets(
            query=query,
            max_results=MAX_TWEETS_PER_PRODUCT,  # Max 100 per request
            tweet_fields=['created_at', 'text', 'author_id'],
            expansions=['author_id']
        )

        # Tweepy returns tweets and user data separately, so we need to map them.
        if response.data and response.includes and 'users' in response.includes:
            users = {user["id"]: user for user in response.includes['users']}
            for tweet in response.data:
                # Ensure the author_id from the tweet exists in our users dictionary
                if tweet.author_id in users:
                    author = users[tweet.author_id]
                    all_tweets.append({
                        'product_id': product_id,
                        'source': 'Twitter',
                        'date': tweet.created_at,
                        'text': tweet.text,
                        'username': author.username
                    })
        # A small delay to be respectful to the API
        time.sleep(1) 
        
    except Exception as e:
        print(f"  ⚠️ Warning: Could not scrape tweets for '{row['search_term']}'. Error: {e}")

if all_tweets:
    pd.DataFrame(all_tweets).to_csv(TWEETS_OUTPUT_FILE, index=False)
    print(f"Success: Scraped a total of {len(all_tweets)} tweets and saved to '{TWEETS_OUTPUT_FILE}'.")
else:
    print("No tweets found for any product. (Note: Twitter's free API only searches the last 7 days).")

# --- Section 5: Scrape Reddit Data (No changes needed here) ---
print("\nStep 3: Scraping Reddit...")
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
            # Limiting to 100 per subreddit for each product to match twitter's limit
            # You might get more than 100 total if a product is in multiple subreddits
            limit_per_sub = (MAX_POSTS_PER_PRODUCT // len(SUBREDDITS_TO_SEARCH)) + 1
            for submission in subreddit.search(reddit_query, limit=limit_per_sub, sort='new'):
                all_reddit_posts.append({'product_id': product_id, 'source': 'Reddit', 'date': pd.to_datetime(submission.created_utc, unit='s'), 'text': f"{submission.title} {submission.selftext}", 'username': submission.author.name if submission.author else '[deleted]'})
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ Warning: Could not scrape subreddit '{subreddit_name}'. Error: {e}")
if all_reddit_posts:
    reddit_df = pd.DataFrame(all_reddit_posts)
    # Deduplicate posts that might be crossposted or appear in multiple searches
    reddit_df.drop_duplicates(subset=['text'], inplace=True, keep='first')
    reddit_df.to_csv(REDDIT_OUTPUT_FILE, index=False)
    print(f"Success: Scraped a total of {len(reddit_df)} Reddit posts and saved to '{REDDIT_OUTPUT_FILE}'.")
else:
    print("No Reddit posts found for any product.")

print("\n--- Social Media Scraping Complete ---")