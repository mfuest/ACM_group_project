#!/usr/bin/env python3
"""
Ingest Arctic Shift comments JSONL -> Parquet (streaming).

Usage:
  python scrape/ingest_comments_jsonl.py --in path/to/comments.jsonl --out data/raw/comments.parquet
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def normalize_comment(obj: Dict[str, Any]) -> Dict[str, Any]:
    comment_id = obj.get("id")
    created_utc = obj.get("created_utc") or obj.get("created") or obj.get("createdAt")
    author = obj.get("author")
    body = obj.get("body") or obj.get("selftext")
    score = obj.get("score")

    link_id = obj.get("link_id")  # usually "t3_<postid>"
    parent_id = obj.get("parent_id")  # "t3_<postid>" or "t1_<commentid>"
    permalink = obj.get("permalink")

    # Extract post_id if link_id is present
    post_id = None
    if isinstance(link_id, str) and link_id.startswith("t3_"):
        post_id = link_id[3:]

    return {
        "comment_id": comment_id,
        "post_id": post_id,         # derived
        "link_id": link_id,         # keep raw too
        "parent_id": parent_id,
        "created_utc": int(created_utc) if created_utc is not None else None,
        "author": author,
        "body": body,
        "score": score,
        "permalink": permalink,
    }


def write_parquet_stream(records: List[Dict[str, Any]], writer: Optional[pq.ParquetWriter], out_path: Path):
    df = pd.DataFrame.from_records(records)

    if "comment_id" in df.columns:
        df = df.drop_duplicates(subset=["comment_id"])

    table = pa.Table.from_pandas(df, preserve_index=False)

    if writer is None:
        writer = pq.ParquetWriter(out_path.as_posix(), table.schema, compression="snappy")
    writer.write_table(table)
    return writer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Path to comments.jsonl")
    ap.add_argument("--out", required=True, help="Output parquet path")
    ap.add_argument("--chunk", type=int, default=100_000, help="Number of lines per write chunk")
    args = ap.parse_args()

    in_path = Path(args.inp)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists():
        out_path.unlink()

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
                buf.append(normalize_comment(obj))
                n += 1
            except Exception:
                bad += 1

            if len(buf) >= args.chunk:
                writer = write_parquet_stream(buf, writer, out_path)
                buf = []
                print(f"[comments] ingested {n:,} lines (bad {bad})")

    if buf:
        writer = write_parquet_stream(buf, writer, out_path)

    if writer is not None:
        writer.close()

    print(f"[comments] DONE. lines={n:,} bad={bad} out={out_path.resolve()}")


if __name__ == "__main__":
    main()
