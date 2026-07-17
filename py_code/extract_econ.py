"""
Download OpenAlex works for one publication year in the Economics field.

Queries the OpenAlex API for every work whose primary topic is in the
"Economics, Econometrics and Finance" field (id 20) for one year, and writes the
raw JSON of each work -- one record per line -- to a gzip JSON Lines archive.
The archive is the immutable source layer; build_parquet.py turns it into the
analysis dataset, so new columns can be added later without re-downloading.

Run on a Narval LOGIN node (compute nodes have no internet), inside tmux so it
survives a disconnect. run_extraction.sh drives this over a range of years.

    python extract_econ.py --year 2020 --out-dir /scratch/.../archive

OpenAlex meters the API in daily credits (one list call = one credit; a free
account key allows 10,000/day, no key only 1,000/day). The key is read from
OPENALEX_API_KEY or ~/.openalex_api_key and is never stored in the repo. Before
a year starts, the script checks its size against the remaining quota and sleeps
until the midnight-UTC reset if it would not fit, so a year is never cut off
mid-download.
"""

import argparse
import gzip
import json
import math
import os
import time

import requests

MAILTO = "hridanshkhaitan@gmail.com"   # OpenAlex "polite pool" contact
ECONOMICS_FIELD_ID = 20

API_URL = "https://api.openalex.org/works"
PER_PAGE = 200        # maximum works per call
MAX_RETRIES = 10      # retries per page before giving up on the year
MAX_WAIT = 60         # cap on backoff between retries (seconds)
REQUEST_PAUSE = 0.15  # pause after each successful call (seconds)

# Latest rate-limit state reported by the API, updated on every response.
quota = {"remaining": None, "reset_seconds": None}


def get_api_key():
    """Return the API key from OPENALEX_API_KEY, then ~/.openalex_api_key, else ''."""
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
    """Query parameters shared by every call for one year."""
    params = {
        "filter": f"publication_year:{year},primary_topic.field.id:fields/{ECONOMICS_FIELD_ID}",
        "mailto": MAILTO,
    }
    if API_KEY:
        params["api_key"] = API_KEY
    return params


def update_quota(response):
    """Record the daily quota from a response's rate-limit headers."""
    remaining = response.headers.get("x-ratelimit-remaining")
    reset_seconds = response.headers.get("x-ratelimit-reset")
    if remaining is not None:
        quota["remaining"] = int(remaining)
    if reset_seconds is not None:
        quota["reset_seconds"] = int(reset_seconds)


def fetch_page(year, cursor):
    """Fetch one page from the API, retrying transient failures with backoff.

    Rate-limit (429), server (5xx), and network errors are retried; a 429 whose
    Retry-After signals a quota reset is waited out so the year finishes the next
    day. Raises RuntimeError if the page still fails after MAX_RETRIES.
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

        response.raise_for_status()   # a genuine 4xx: do not retry

    raise RuntimeError(f"[{year}] still failing after {MAX_RETRIES} retries; aborting this year")


def calls_needed(year):
    """Return (work count, pages required) for a year from a cheap 1-result query."""
    params = dict(base_params(year), **{"per-page": 1})
    response = requests.get(API_URL, params=params, timeout=60)
    update_quota(response)
    response.raise_for_status()
    count = response.json()["meta"]["count"]
    return count, math.ceil(count / PER_PAGE) + 3


def wait_for_quota(year, needed):
    """Sleep until the quota resets if the year would not fit in what's left today.

    A long mid-year pause would invalidate the pagination cursor, so it is better
    to wait for the reset before starting than to be interrupted partway.
    """
    if quota["remaining"] is None or quota["remaining"] >= needed:
        return
    pause = (quota["reset_seconds"] or 0) + 120
    print(f"[{year}] needs ~{needed} calls but only {quota['remaining']} left today; "
          f"sleeping {pause/3600:.1f}h until quota resets")
    time.sleep(pause)


def extract_year(year, out_dir):
    """Download all Economics works for one year into a gzip JSONL archive."""
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
            if calls % 25 == 0:
                print(f"[{year}] {total}/{count} works | {int(time.time() - start)}s")
            cursor = page.get("meta", {}).get("next_cursor")
            time.sleep(REQUEST_PAUSE)

    # Marker written only after a clean finish; run_extraction.sh skips years
    # that already have one, so re-runs resume where they stopped.
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
