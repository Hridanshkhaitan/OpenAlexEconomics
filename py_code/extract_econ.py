"""
Extract OpenAlex works for a single publication year in the Economics field.

This script queries the OpenAlex API for every work whose primary topic falls
in the "Economics, Econometrics and Finance" field (OpenAlex field id 20) for
one publication year, and writes the raw JSON of each work -- one record per
line -- to a gzip-compressed JSON Lines file. This file is the immutable
"archive" layer: it is never edited after download.

Analysis-ready columns are produced separately by build_parquet.py, which reads
these archive files. Keeping the raw archive means new columns can be added
later by re-processing the archive, without re-downloading from the API.

Run this on a Narval LOGIN node (compute nodes have no internet access),
ideally inside a tmux/screen session so it survives a disconnect.

Usage:
    python extract_econ.py --year 2020 --out-dir /scratch/hridansh/openalex_econ_download/archive

Notes:
    - OpenAlex does not use API keys. Access to the faster "polite pool" is
      granted by sending a contact email via the `mailto` parameter.
    - Results are paginated with a cursor; we request 200 works per call.
"""

import argparse
import gzip
import json
import os
import time

import requests

# Contact email for the OpenAlex "polite pool" (faster, more reliable access).
MAILTO = "hridanshkhaitan@gmail.com"

# OpenAlex field id for "Economics, Econometrics and Finance".
ECONOMICS_FIELD_ID = 20

API_URL = "https://api.openalex.org/works"
PER_PAGE = 200      # Maximum works OpenAlex returns per call.
MAX_RETRIES = 5     # Retries per page before giving up.


def fetch_page(year, cursor):
    """Fetch one page of results from the OpenAlex API.

    Retries with exponential backoff on rate-limit (429) or server (5xx) errors.

    Args:
        year: Publication year to filter on.
        cursor: Pagination cursor ("*" for the first page).

    Returns:
        The parsed JSON response as a dict.

    Raises:
        requests.HTTPError: If the request keeps failing after MAX_RETRIES.
    """
    params = {
        "filter": f"publication_year:{year},primary_topic.field.id:fields/{ECONOMICS_FIELD_ID}",
        "per-page": PER_PAGE,
        "cursor": cursor,
        "mailto": MAILTO,
    }
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.get(API_URL, params=params, timeout=60)
        if response.status_code == 200:
            return response.json()
        wait = 2 ** attempt
        print(f"  [{year}] HTTP {response.status_code} (attempt {attempt}); retrying in {wait}s")
        time.sleep(wait)
    response.raise_for_status()


def extract_year(year, out_dir):
    """Download all Economics works for one year into a gzip JSONL archive.

    Args:
        year: Publication year to download.
        out_dir: Directory where the archive file is written.
    """
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"econ_{year}.jsonl.gz")

    cursor = "*"
    total = 0
    calls = 0
    start = time.time()
    print(f"[{year}] starting download -> {out_path}")

    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        while cursor:
            page = fetch_page(year, cursor)
            results = page.get("results", [])
            if not results:
                break
            for work in results:
                f.write(json.dumps(work) + "\n")
            total += len(results)
            calls += 1
            if calls % 25 == 0:   # progress roughly every 5,000 works
                print(f"[{year}] {total} works | {int(time.time() - start)}s")
            cursor = page.get("meta", {}).get("next_cursor")

    print(f"[{year}] DONE: {total} works in {int(time.time() - start)}s -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Download OpenAlex Economics works for one year.")
    parser.add_argument("--year", type=int, required=True, help="Publication year to download.")
    parser.add_argument("--out-dir", required=True, help="Output directory for the .jsonl.gz archive.")
    args = parser.parse_args()
    extract_year(args.year, args.out_dir)


if __name__ == "__main__":
    main()
