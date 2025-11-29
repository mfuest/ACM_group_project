"""
Reddit Scraper for Political Polarization Research
===================================================

This script scrapes Reddit posts from country-specific subreddits (r/de, r/thenetherlands, r/france)
during three time periods: pre-EURO, during EURO, and post-EURO 2024.

The script:
1. Authenticates with Reddit API using praw and credentials from .env
2. Fetches posts from specified subreddits within date ranges
3. Filters posts based on political keywords
4. Exports raw and filtered data to CSV files

Usage:
    python scripts/reddit_scraper.py
"""

import os
import praw
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path
import time

# Load environment variables
load_dotenv()

# Define project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_CLEAN = PROJECT_ROOT / "data" / "clean"

# Ensure directories exist
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_CLEAN.mkdir(parents=True, exist_ok=True)

# Reddit API configuration
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "PoliticalPolarizationResearch/1.0")

# Subreddit mapping
SUBREDDITS = {
    "germany": "de",
    "netherlands": "thenetherlands",
    "france": "france"
}

# Time windows for data collection
TIME_WINDOWS = {
    "pre_euro": {
        "start": datetime(2024, 5, 15, tzinfo=timezone.utc),
        "end": datetime(2024, 6, 13, 23, 59, 59, tzinfo=timezone.utc)
    },
    "during_euro": {
        "start": datetime(2024, 6, 14, tzinfo=timezone.utc),
        "end": datetime(2024, 7, 14, 23, 59, 59, tzinfo=timezone.utc)
    },
    "post_euro": {
        "start": datetime(2024, 7, 15, tzinfo=timezone.utc),
        "end": datetime(2024, 8, 15, 23, 59, 59, tzinfo=timezone.utc)
    }
}

# Political keywords for filtering
POLITICAL_KEYWORDS = {
    "germany": [
        "afd", "cdu", "spd", "csu", "gruene", "grüne", "linke",
        "merz", "scholz", "habeck", "migration", "flüchtlinge",
        "asyl", "klima", "heizungsgesetz", "bundestag", "ampel"
    ],
    "netherlands": [
        "vvd", "d66", "pvv", "wilders", "rutte", "klimaat",
        "immigratie", "verkiezingen", "kabinet"
    ],
    "france": [
        "macron", "rn", "mélenchon", "melenchon", "immigration",
        "climat", "gouvernement", "élection", "election", "assemblée", "assemblee"
    ]
}


def initialize_reddit():
    """
    Initialize Reddit API client using credentials from .env file.
    
    Returns:
        praw.Reddit: Authenticated Reddit instance
        
    Raises:
        ValueError: If required credentials are missing
    """
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError(
            "Missing Reddit API credentials. Please set REDDIT_CLIENT_ID and "
            "REDDIT_CLIENT_SECRET in your .env file."
        )
    
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    
    # Test connection
    try:
        reddit.user.me()
        print("✓ Successfully authenticated with Reddit API")
    except Exception:
        print("✓ Reddit API client initialized (read-only mode)")
    
    return reddit


def is_political_post(post, keywords):
    """
    Check if a post contains any political keywords.
    
    Args:
        post: praw.models.Submission object
        keywords: List of keywords to search for
        
    Returns:
        bool: True if post contains political keywords
    """
    text_to_search = f"{post.title} {post.selftext}".lower()
    return any(keyword.lower() in text_to_search for keyword in keywords)


def fetch_posts(reddit, subreddit_name, start_date, end_date, max_posts=1000):
    """
    Fetch posts from a subreddit within a date range.
    
    Note: Reddit's API has limitations for historical data. This function uses
    multiple strategies to collect posts:
    1. Search by timestamp range (for historical data)
    2. Fetch new posts (for recent data)
    3. Fetch top posts (for popular content)
    
    Args:
        reddit: Authenticated praw.Reddit instance
        subreddit_name: Name of the subreddit (without r/)
        start_date: datetime object for start of time window
        end_date: datetime object for end of time window
        max_posts: Maximum number of posts to fetch
        
    Returns:
        list: List of praw.models.Submission objects
    """
    subreddit = reddit.subreddit(subreddit_name)
    posts = []
    seen_ids = set()  # Track post IDs to avoid duplicates
    
    print(f"  Fetching posts from r/{subreddit_name}...")
    
    try:
        # Convert dates to Unix timestamps for Reddit search
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        # Strategy 1: Use Reddit search with timestamp range
        # Format: timestamp:start..end
        search_query = f"timestamp:{start_timestamp}..{end_timestamp}"
        try:
            print(f"  Searching with timestamp range...")
            for post in subreddit.search(search_query, limit=max_posts, sort="new"):
                if post.id not in seen_ids:
                    post_date = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                    if start_date <= post_date <= end_date:
                        posts.append(post)
                        seen_ids.add(post.id)
                time.sleep(0.1)
        except Exception as e:
            print(f"  Note: Search API limitation: {e}")
        
        # Strategy 2: Fetch new posts (works for recent data)
        # Only use if the end date is recent (within last 30 days)
        now = datetime.now(timezone.utc)
        days_ago = (now - end_date).days
        if days_ago <= 30:
            try:
                print(f"  Fetching recent posts...")
                for post in subreddit.new(limit=min(max_posts, 1000)):
                    if post.id not in seen_ids:
                        post_date = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                        # Stop if we've gone past the start date
                        if post_date < start_date:
                            break
                        # Include posts within the date range
                        if start_date <= post_date <= end_date:
                            posts.append(post)
                            seen_ids.add(post.id)
                    time.sleep(0.1)
            except Exception as e:
                print(f"  Note: Error fetching new posts: {e}")
        
        # Strategy 3: Fetch top posts from different time periods
        # Try different time filters if the date range spans multiple periods
        time_filters = ["all", "year", "month", "week", "day"]
        for time_filter in time_filters:
            try:
                print(f"  Fetching top posts ({time_filter})...")
                for post in subreddit.top(time_filter=time_filter, limit=500):
                    if post.id not in seen_ids:
                        post_date = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                        if start_date <= post_date <= end_date:
                            posts.append(post)
                            seen_ids.add(post.id)
                    time.sleep(0.1)
            except Exception as e:
                print(f"  Note: Error fetching top posts ({time_filter}): {e}")
        
        print(f"  Found {len(posts)} unique posts in date range")
        
    except Exception as e:
        print(f"  Error fetching posts: {e}")
        import traceback
        traceback.print_exc()
    
    return posts


def post_to_dict(post):
    """
    Convert a praw Submission object to a dictionary.
    
    Args:
        post: praw.models.Submission object
        
    Returns:
        dict: Dictionary containing post data
    """
    return {
        "id": post.id,
        "title": post.title,
        "selftext": post.selftext,
        "author": str(post.author) if post.author else "[deleted]",
        "created_utc": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
        "score": post.score,
        "upvote_ratio": post.upvote_ratio,
        "num_comments": post.num_comments,
        "url": post.url,
        "permalink": f"https://reddit.com{post.permalink}",
        "subreddit": str(post.subreddit),
        "is_self": post.is_self,
        "over_18": post.over_18
    }


def scrape_country_phase(reddit, country, phase):
    """
    Scrape posts for a specific country and time phase.
    
    Args:
        reddit: Authenticated praw.Reddit instance
        country: Country name (germany, netherlands, france)
        phase: Time phase (pre_euro, during_euro, post_euro)
    """
    subreddit_name = SUBREDDITS[country]
    time_window = TIME_WINDOWS[phase]
    keywords = POLITICAL_KEYWORDS[country]
    
    print(f"\n[{country.upper()}] [{phase.upper()}]")
    print(f"  Date range: {time_window['start'].date()} to {time_window['end'].date()}")
    
    # Fetch posts
    posts = fetch_posts(
        reddit,
        subreddit_name,
        time_window["start"],
        time_window["end"]
    )
    
    if not posts:
        print(f"  No posts found for {country} in {phase}")
        return
    
    # Convert to DataFrame
    posts_data = [post_to_dict(post) for post in posts]
    df_raw = pd.DataFrame(posts_data)
    
    # Save raw data
    raw_filename = DATA_RAW / f"{country}_{phase}.csv"
    df_raw.to_csv(raw_filename, index=False)
    print(f"  ✓ Saved {len(df_raw)} raw posts to {raw_filename}")
    
    # Filter political posts
    political_posts = [
        post for post in posts
        if is_political_post(post, keywords)
    ]
    
    if political_posts:
        political_data = [post_to_dict(post) for post in political_posts]
        df_political = pd.DataFrame(political_data)
        
        # Save filtered data
        clean_filename = DATA_CLEAN / f"{country}_{phase}_politics.csv"
        df_political.to_csv(clean_filename, index=False)
        print(f"  ✓ Saved {len(df_political)} political posts to {clean_filename}")
    else:
        print(f"  No political posts found for {country} in {phase}")


def main():
    """
    Main function to orchestrate the scraping process.
    """
    print("=" * 60)
    print("Reddit Scraper for Political Polarization Research")
    print("=" * 60)
    
    # Initialize Reddit API
    try:
        reddit = initialize_reddit()
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Scrape data for each country and phase
    countries = ["germany", "netherlands", "france"]
    phases = ["pre_euro", "during_euro", "post_euro"]
    
    for country in countries:
        for phase in phases:
            try:
                scrape_country_phase(reddit, country, phase)
                # Be respectful to Reddit API
                time.sleep(2)
            except Exception as e:
                print(f"  Error scraping {country} {phase}: {e}")
                continue
    
    print("\n" + "=" * 60)
    print("Scraping complete!")
    print("=" * 60)
    print(f"\nRaw data saved to: {DATA_RAW}")
    print(f"Filtered data saved to: {DATA_CLEAN}")


if __name__ == "__main__":
    main()

