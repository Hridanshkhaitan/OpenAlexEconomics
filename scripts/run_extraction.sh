#!/bin/bash
#
# Download OpenAlex Economics works for a range of years, running several years
# in parallel. Each year is handled by extract_econ.py and written to its own
# gzip JSONL archive file.
#
# Run this on a Narval LOGIN node (compute nodes have no internet access),
# ideally inside a tmux/screen session so it survives a disconnect.
#
# Usage:
#   ./run_extraction.sh 1960 2025
#
# MAX_PARALLEL controls how many years download at once. Keep it modest so the
# combined request rate stays within OpenAlex's ~10 requests/second polite pool.

set -euo pipefail

START_YEAR=${1:?usage: run_extraction.sh START_YEAR END_YEAR}
END_YEAR=${2:?usage: run_extraction.sh START_YEAR END_YEAR}

# Locate extract_econ.py in the sibling py_code/ directory, so this script
# works no matter which directory it is launched from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTRACT_PY="$SCRIPT_DIR/../py_code/extract_econ.py"

OUT_DIR=/scratch/hridansh/openalex_econ_download/archive
LOG_DIR=/scratch/hridansh/openalex_econ_download/logs
MAX_PARALLEL=8

mkdir -p "$OUT_DIR" "$LOG_DIR"

for year in $(seq "$START_YEAR" "$END_YEAR"); do
    # Wait until fewer than MAX_PARALLEL background jobs are running.
    while [ "$(jobs -rp | wc -l)" -ge "$MAX_PARALLEL" ]; do
        wait -n
    done
    echo "launching year $year"
    python "$EXTRACT_PY" --year "$year" --out-dir "$OUT_DIR" \
        > "$LOG_DIR/econ_${year}.log" 2>&1 &
done

wait
echo "All years complete."
