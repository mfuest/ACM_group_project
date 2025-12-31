#!/usr/bin/env python3
"""
Ingest Arctic Shift posts JSONL -> Parquet (streaming).

Usage:
  python scrape/ingest_posts_jsonl.py --in path/to/posts.jsonl --out data/raw/posts.parquet
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def normalize_post(obj: Dict[str, Any]) -> Dict[str, Any]:
    # Be defensive: different exports sometimes use slightly different keys.
    post_id = obj.get("id")
    created_utc = obj.get("created_utc") or obj.get("created") or obj.get("createdAt")
    title = obj.get("title")
    selftext = obj.get("selftext") or obj.get("body")  # sometimes "body" for text posts
    author = obj.get("author")
    permalink = obj.get("permalink")
    url = obj.get("url")
    flair = obj.get("link_flair_text") or obj.get("flair") or obj.get("link_flair")
    score = obj.get("score")
    num_comments = obj.get("num_comments")

    # useful join key
    post_fullname = f"t3_{post_id}" if post_id else None

    return {
        "post_id": post_id,
        "created_utc": int(created_utc) if created_utc is not None else None,
        "title": title,
        "selftext": selftext,
        "author": author,
        "permalink": permalink,
        "url": url,
        "flair": flair,
        "score": score,
        "num_comments": num_comments,
        "post_fullname": post_fullname,
    }


def write_parquet_stream(records: List[Dict[str, Any]], writer: Optional[pq.ParquetWriter], out_path: Path):
    df = pd.DataFrame.from_records(records)

    # Basic dedupe on post_id within chunk
    if "post_id" in df.columns:
        df = df.drop_duplicates(subset=["post_id"])

    table = pa.Table.from_pandas(df, preserve_index=False)

    if writer is None:
        writer = pq.ParquetWriter(out_path.as_posix(), table.schema, compression="snappy")
    writer.write_table(table)
    return writer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Path to posts.jsonl")
    ap.add_argument("--out", required=True, help="Output parquet path")
    ap.add_argument("--chunk", type=int, default=50_000, help="Number of lines per write chunk")
    args = ap.parse_args()

    in_path = Path(args.inp)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists():
        out_path.unlink()  # avoid accidental appends from previous runs

    writer = None
    buf: List[Dict[str, Any]] = []
    n = 0
    bad = 0

    with in_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                buf.append(normalize_post(obj))
                n += 1
            except Exception:
                bad += 1

            if len(buf) >= args.chunk:
                writer = write_parquet_stream(buf, writer, out_path)
                buf = []
                print(f"[posts] ingested {n:,} lines (bad {bad})")

    if buf:
        writer = write_parquet_stream(buf, writer, out_path)

    if writer is not None:
        writer.close()

    print(f"[posts] DONE. lines={n:,} bad={bad} out={out_path.resolve()}")


if __name__ == "__main__":
    main()
