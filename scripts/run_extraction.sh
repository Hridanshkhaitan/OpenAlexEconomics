#!/bin/bash
#
# Download OpenAlex Economics works for a range of years, one year at a time.
# Each year is handled by extract_econ.py and written to its own gzip JSONL
# archive file.
#
# Years run SEQUENTIALLY on purpose: OpenAlex meters usage as a daily credit
# quota, so parallel workers only race each other into the same limit. A
# single worker uses the whole day's quota by itself, and extract_econ.py
# sleeps over the midnight-UTC quota reset when needed -- so this script can
# simply be left running in tmux for several days until all years are done.
#
# Run this on a Narval LOGIN node (compute nodes have no internet access),
# inside a tmux/screen session so it survives a disconnect.
#
# Usage:
#   ./run_extraction.sh 1647 2025

set -euo pipefail

START_YEAR=${1:?usage: run_extraction.sh START_YEAR END_YEAR}
END_YEAR=${2:?usage: run_extraction.sh START_YEAR END_YEAR}

# Locate extract_econ.py in the sibling py_code/ directory, so this script
# works no matter which directory it is launched from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTRACT_PY="$SCRIPT_DIR/../py_code/extract_econ.py"

OUT_DIR=/scratch/hridansh/openalex_econ_download/archive
LOG_DIR=/scratch/hridansh/openalex_econ_download/logs

mkdir -p "$OUT_DIR" "$LOG_DIR"

for year in $(seq "$START_YEAR" "$END_YEAR"); do
    # Skip years already downloaded in full (a .done marker was written).
    if [ -f "$OUT_DIR/econ_${year}.done" ]; then
        echo "skipping year $year (already complete)"
        continue
    fi
    echo "starting year $year"
    # -u = unbuffered output, so per-year logs update live (and nothing is lost
    # if a worker is interrupted). A failed year is reported but does not stop
    # the remaining years; re-running the same command later retries it.
    if ! python -u "$EXTRACT_PY" --year "$year" --out-dir "$OUT_DIR" \
            2>&1 | tee "$LOG_DIR/econ_${year}.log"; then
        echo "year $year FAILED -- see $LOG_DIR/econ_${year}.log"
    fi
done

echo "All years complete."
