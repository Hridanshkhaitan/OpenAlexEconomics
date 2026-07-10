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

API key and daily quota:
    OpenAlex meters API usage in daily credits (a "list" call costs 1 credit;
    a free account key grants 10,000/day vs only 1,000/day without a key).
    The key is read from the OPENALEX_API_KEY environment variable, or from
    the file ~/.openalex_api_key if the variable is not set. It is never
    stored in this repository.

    Before downloading a year, the script estimates how many calls the year
    needs; if today's remaining quota is too small, it sleeps until the quota
    resets (midnight UTC) and then starts. This way a year is never cut off
    in the middle of its download.
"""

import argparse
import gzip
import json
import math
import os
import time

import requests

# Contact email for the OpenAlex "polite pool" (faster, more reliable access).
MAILTO = "hridanshkhaitan@gmail.com"

# OpenAlex field id for "Economics, Econometrics and Finance".
ECONOMICS_FIELD_ID = 20

API_URL = "https://api.openalex.org/works"
PER_PAGE = 200        # Maximum works OpenAlex returns per call.
MAX_RETRIES = 10      # Retries per page before giving up on the year.
MAX_WAIT = 60         # Cap on backoff wait between retries (seconds).
REQUEST_PAUSE = 0.15  # Polite pause after each successful call (seconds).

# Most recent rate-limit info reported by the API (updated on every response).
quota = {"remaining": None, "reset_seconds": None}


def get_api_key():
    """Return the OpenAlex API key from the environment or key file.

    Looks at the OPENALEX_API_KEY environment variable first, then at the
    file ~/.openalex_api_key. Returns an empty string if neither exists
    (the script then runs on the small no-key quota).
    """
    key = os.environ.get("OPENALEX_API_KEY", "").strip()
    if key:
        return key
    key_file = os.path.expanduser("~/.openalex_api_key")
    if os.path.exists(key_file):
        with open(key_file) as f:
            return f.read().strip()
    return ""


API_KEY = get_api_key()


def base_params(year):
    """Build the query parameters shared by every API call for one year."""
    params = {
        "filter": f"publication_year:{year},primary_topic.field.id:fields/{ECONOMICS_FIELD_ID}",
        "mailto": MAILTO,
    }
    if API_KEY:
        params["api_key"] = API_KEY
    return params


def update_quota(response):
    """Record the daily quota state from a response's rate-limit headers."""
    remaining = response.headers.get("x-ratelimit-remaining")
    reset_seconds = response.headers.get("x-ratelimit-reset")
    if remaining is not None:
        quota["remaining"] = int(remaining)
    if reset_seconds is not None:
        quota["reset_seconds"] = int(reset_seconds)


def fetch_page(year, cursor):
    """Fetch one page of results from the OpenAlex API.

    Retryable failures (rate-limit 429, server 5xx, network errors) are retried
    with exponential backoff. If the daily quota runs out mid-year despite the
    up-front check, the server's Retry-After (time until the quota resets) is
    honoured so the year can finish the next day.

    Args:
        year: Publication year to filter on.
        cursor: Pagination cursor ("*" for the first page).

    Returns:
        The parsed JSON response as a dict.

    Raises:
        RuntimeError: If the page still cannot be fetched after MAX_RETRIES.
    """
    params = dict(base_params(year), **{"per-page": PER_PAGE, "cursor": cursor})
    wait = 2
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(API_URL, params=params, timeout=60)
        except requests.RequestException as exc:
            print(f"  [{year}] network error ({exc}); retry {attempt}/{MAX_RETRIES} in {wait}s")
            time.sleep(wait)
            wait = min(wait * 2, MAX_WAIT)
            continue

        update_quota(response)
        if response.status_code == 200:
            return response.json()

        # 429 = rate limited, 5xx = transient server error: wait and retry.
        if response.status_code == 429 or response.status_code >= 500:
            retry_after = response.headers.get("Retry-After")
            pause = int(retry_after) if retry_after and retry_after.isdigit() else wait
            if pause > 600:
                print(f"  [{year}] daily quota exhausted; sleeping {pause/3600:.1f}h until it resets")
            else:
                print(f"  [{year}] HTTP {response.status_code}; retry {attempt}/{MAX_RETRIES} in {pause}s")
            time.sleep(pause + 5)
            wait = min(wait * 2, MAX_WAIT)
            continue

        # Any other 4xx is a real error (bad request etc.) -- do not retry.
        response.raise_for_status()

    raise RuntimeError(f"[{year}] still failing after {MAX_RETRIES} retries; aborting this year")


def calls_needed(year):
    """Ask the API how many works the year has and return the calls required.

    Uses a cheap 1-result query to read the total count, then converts it to
    the number of full pages needed (plus a small safety margin).
    """
    params = dict(base_params(year), **{"per-page": 1})
    response = requests.get(API_URL, params=params, timeout=60)
    update_quota(response)
    response.raise_for_status()
    count = response.json()["meta"]["count"]
    return count, math.ceil(count / PER_PAGE) + 3


def wait_for_quota(year, needed):
    """Sleep until the daily quota resets if the year won't fit in what's left.

    This prevents a year's download from being interrupted halfway through
    when the day's credits run out (pagination cursors do not survive a long
    overnight pause).
    """
    if quota["remaining"] is None or quota["remaining"] >= needed:
        return
    pause = (quota["reset_seconds"] or 0) + 120
    print(f"[{year}] needs ~{needed} calls but only {quota['remaining']} left today; "
          f"sleeping {pause/3600:.1f}h until quota resets")
    time.sleep(pause)


def extract_year(year, out_dir):
    """Download all Economics works for one year into a gzip JSONL archive.

    Args:
        year: Publication year to download.
        out_dir: Directory where the archive file is written.
    """
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"econ_{year}.jsonl.gz")
    done_path = os.path.join(out_dir, f"econ_{year}.done")

    count, needed = calls_needed(year)
    print(f"[{year}] {count} works (~{needed} calls); quota remaining today: {quota['remaining']}")
    wait_for_quota(year, needed)

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
                print(f"[{year}] {total}/{count} works | {int(time.time() - start)}s")
            cursor = page.get("meta", {}).get("next_cursor")
            time.sleep(REQUEST_PAUSE)   # stay comfortably within the rate limit

    # Write a completion marker only after the whole year finished cleanly. Its
    # presence lets run_extraction.sh skip already-finished years on a re-run.
    with open(done_path, "w") as marker:
        marker.write(f"{total}\n")
    print(f"[{year}] DONE: {total} works in {int(time.time() - start)}s -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Download OpenAlex Economics works for one year.")
    parser.add_argument("--year", type=int, required=True, help="Publication year to download.")
    parser.add_argument("--out-dir", required=True, help="Output directory for the .jsonl.gz archive.")
    args = parser.parse_args()
    if not API_KEY:
        print("WARNING: no API key found (OPENALEX_API_KEY or ~/.openalex_api_key); "
              "running on the small no-key quota.")
    extract_year(args.year, args.out_dir)


if __name__ == "__main__":
    main()
