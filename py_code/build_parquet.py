"""
Build a curated, analysis-ready Parquet dataset from the OpenAlex archives.

Reads the gzip JSON Lines archives produced by extract_econ.py and extracts a
set of commonly used, typed columns. The output is written as Parquet,
partitioned by publication_year, so a single year or a single column can be
read without loading the whole corpus.

The raw archives remain the source of truth: to add a new column later, extend
extract_work() and re-run this script -- no re-download is needed.

This step only reads local files, so (unlike the download) it can be run on a
Narval compute node.

Usage:
    python build_parquet.py \
        --archive-dir /scratch/hridansh/openalex_econ_download/archive \
        --out-dir /scratch/hridansh/openalex_econ_download/parquet
"""

import argparse
import glob
import gzip
import json
import os
import re

import pandas as pd


def reconstruct_abstract(inverted_index):
    """Rebuild abstract text from OpenAlex's inverted-index representation.

    OpenAlex stores abstracts as {word: [positions]}. This reverses that back
    into readable text.

    Args:
        inverted_index: The abstract_inverted_index dict, or None.

    Returns:
        The abstract as a string, or None if unavailable.
    """
    if not inverted_index:
        return None
    positions = []
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(word for _, word in positions)


def extract_work(work):
    """Extract the curated columns from one OpenAlex work record.

    Args:
        work: A single work dict as returned by the OpenAlex API.

    Returns:
        A flat dict of typed columns for the analysis dataset.
    """
    topic = work.get("primary_topic") or {}
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    authorships = work.get("authorships") or []
    open_access = work.get("open_access") or {}

    return {
        "id": (work.get("id") or "").replace("https://openalex.org/", ""),
        "doi": work.get("doi"),
        "title": work.get("title"),
        "publication_year": work.get("publication_year"),
        "publication_date": work.get("publication_date"),
        "type": work.get("type"),
        "language": work.get("language"),
        "cited_by_count": work.get("cited_by_count"),
        "field": (topic.get("field") or {}).get("display_name"),
        "subfield": (topic.get("subfield") or {}).get("display_name"),
        "primary_topic": topic.get("display_name"),
        "author_count": len(authorships),
        "first_author": authorships[0].get("raw_author_name") if authorships else None,
        "journal": source.get("display_name"),
        "is_oa": open_access.get("is_oa"),
        "referenced_works_count": len(work.get("referenced_works") or []),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
    }


def build_year(archive_path, out_dir):
    """Convert one archive file into one Parquet partition.

    Args:
        archive_path: Path to an econ_<year>.jsonl.gz archive file.
        out_dir: Root output directory for the partitioned Parquet dataset.
    """
    year = re.search(r"econ_(\d+)\.jsonl\.gz$", os.path.basename(archive_path)).group(1)

    rows = []
    with gzip.open(archive_path, "rt", encoding="utf-8") as f:
        for line in f:
            rows.append(extract_work(json.loads(line)))

    df = pd.DataFrame(rows)
    part_dir = os.path.join(out_dir, f"publication_year={year}")
    os.makedirs(part_dir, exist_ok=True)
    out_path = os.path.join(part_dir, "part-000.parquet")
    df.to_parquet(out_path, engine="pyarrow", compression="zstd", index=False)
    print(f"{os.path.basename(archive_path)}: {len(df)} rows -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Build curated Parquet from OpenAlex archives.")
    parser.add_argument("--archive-dir", required=True, help="Directory of econ_<year>.jsonl.gz files.")
    parser.add_argument("--out-dir", required=True, help="Output directory for the Parquet dataset.")
    args = parser.parse_args()

    archives = sorted(glob.glob(os.path.join(args.archive_dir, "econ_*.jsonl.gz")))
    if not archives:
        print(f"No archive files found in {args.archive_dir}")
        return
    for archive_path in archives:
        build_year(archive_path, args.out_dir)


if __name__ == "__main__":
    main()
