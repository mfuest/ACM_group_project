#!/usr/bin/env python3
"""
Sanity checks for posts/comments parquet.

Usage:
  python scrape/sanity_checks.py --posts data/raw/posts.parquet --comments data/raw/comments.parquet
"""

import argparse
from datetime import datetime, timezone

import pandas as pd


def dt_utc(ts: int) -> str:
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", required=True)
    ap.add_argument("--comments", required=True)
    args = ap.parse_args()

    posts = pd.read_parquet(args.posts)
    comments = pd.read_parquet(args.comments)

    print(f"posts rows: {len(posts):,}")
    print(f"comments rows: {len(comments):,}")

    if len(posts) > 0:
        print("posts time range:",
              dt_utc(posts["created_utc"].min()),
              "→",
              dt_utc(posts["created_utc"].max()))

    if len(comments) > 0:
        print("comments time range:",
              dt_utc(comments["created_utc"].min()),
              "→",
              dt_utc(comments["created_utc"].max()))

    # Deleted/removed ratio
    if "body" in comments.columns:
        body = comments["body"].fillna("")
        deleted = (body == "[deleted]").mean()
        removed = (body == "[removed]").mean()
        print(f"comments deleted: {deleted:.2%}, removed: {removed:.2%}")

    # Join coverage
    if "post_id" in posts.columns and "post_id" in comments.columns:
        post_ids = set(posts["post_id"].dropna().astype(str))
        matched = comments["post_id"].astype(str).isin(post_ids).mean()
        print(f"comments with matching post_id: {matched:.2%}")

    # Daily counts
    for name, df in [("posts", posts), ("comments", comments)]:
        if "created_utc" not in df.columns or df.empty:
            continue
        day = pd.to_datetime(df["created_utc"], unit="s", utc=True).dt.date
        counts = day.value_counts().sort_index()
        print(f"\n{name} daily counts (first 10 days):")
        print(counts.head(10).to_string())
        print(f"{name} daily counts (last 10 days):")
        print(counts.tail(10).to_string())


if __name__ == "__main__":
    main()
