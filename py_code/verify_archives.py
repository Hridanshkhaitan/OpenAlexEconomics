"""
Verify downloaded OpenAlex Economics archives.

For every completed year (one with a .done marker) in a directory, this
script re-reads the whole econ_<year>.jsonl.gz file and checks that:
  - every line is valid JSON (also proves the gzip file is intact),
  - the number of records matches the count in the .done marker,
  - every work id is unique within the year,
  - every record has the right publication_year and the Economics field.

It also lists any .jsonl.gz files WITHOUT a .done marker -- those are
in-progress or leftover partial downloads and should not be trusted.

Usage:
    python verify_archives.py --archive-dir /scratch/hridansh/openalex_econ_download/archive
"""

import argparse
import glob
import gzip
import json
import os

ECONOMICS_FIELD_SUFFIX = "fields/20"


def verify_year(archive_path, expected_count):
    """Fully re-read one year's archive and return a result summary dict."""
    year = int(os.path.basename(archive_path)[5:9])
    lines = 0
    wrong = 0
    ids = set()
    for line in gzip.open(archive_path, "rt", encoding="utf-8"):
        work = json.loads(line)
        lines += 1
        ids.add(work.get("id"))
        field_id = ((work.get("primary_topic") or {}).get("field") or {}).get("id", "")
        if work.get("publication_year") != year or not field_id.endswith(ECONOMICS_FIELD_SUFFIX):
            wrong += 1
    passed = lines == expected_count and len(ids) == lines and wrong == 0
    return {"year": year, "lines": lines, "expected": expected_count,
            "unique": len(ids), "wrong": wrong, "passed": passed}


def main():
    parser = argparse.ArgumentParser(description="Verify OpenAlex Economics archives.")
    parser.add_argument("--archive-dir", required=True, help="Directory with econ_<year>.jsonl.gz files.")
    args = parser.parse_args()

    all_ok = True
    # "**" also matches archives organized into subfolders (e.g. one per century).
    for done in sorted(glob.glob(os.path.join(args.archive_dir, "**", "econ_*.done"),
                                 recursive=True)):
        expected = int(open(done).read().strip())
        result = verify_year(done.replace(".done", ".jsonl.gz"), expected)
        status = "OK  " if result["passed"] else "FAIL"
        all_ok = all_ok and result["passed"]
        print(f"{status} {result['year']}: {result['lines']:,} records "
              f"(marker {result['expected']:,}) | unique {result['unique']:,} | "
              f"wrong year/field: {result['wrong']}")

    unfinished = [f for f in glob.glob(os.path.join(args.archive_dir, "**", "econ_*.jsonl.gz"),
                                       recursive=True)
                  if not os.path.exists(f.replace(".jsonl.gz", ".done"))]
    for f in sorted(unfinished):
        print(f"IN PROGRESS / PARTIAL (no .done marker): {os.path.basename(f)}")

    print("\nALL VERIFIED" if all_ok and not unfinished else "\nCHECK THE LINES ABOVE")


if __name__ == "__main__":
    main()
