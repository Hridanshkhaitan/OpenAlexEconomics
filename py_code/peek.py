"""
Quickly look at the Economics Parquet data from the command line.

Prints a readable preview of one year (or of the whole dataset), and can export
a year or a sample to CSV so it can be opened in Excel / Numbers.

Examples:
    # first 20 rows of 2020, a sensible set of columns
    python peek.py 2020

    # 50 rows, choose the columns yourself
    python peek.py 2020 --rows 50 --cols title,journal,cited_by_count

    # rows whose title contains a word (case-insensitive)
    python peek.py 2020 --search inflation

    # save the whole year to a CSV you can open in Excel
    python peek.py 2020 --csv ~/econ_2020.csv

    # dataset-wide summary (row counts per year), no single year needed
    python peek.py --summary

By default the long `abstract` column is hidden so the table stays readable;
add it explicitly with --cols if you want it.
"""

import argparse
import glob
import os

import pandas as pd

DATA_DIR = "/project/def-kmcel/hridansh/openalex_econ/data/parquet"

# Columns shown by default (the wide `abstract` is left out on purpose).
DEFAULT_COLS = ["id", "publication_year", "title", "first_author",
                "author_count", "journal", "cited_by_count", "subfield"]


def year_path(year):
    """Return the Parquet file path for a year, or None if it does not exist."""
    hits = glob.glob(os.path.join(DATA_DIR, "*", f"{year}.parquet"))
    return hits[0] if hits else None


def show_summary():
    """Print how many works each year has, read cheaply from file metadata."""
    import pyarrow.parquet as pq
    rows = []
    for path in glob.glob(os.path.join(DATA_DIR, "*", "*.parquet")):
        year = int(os.path.basename(path)[:-len(".parquet")])
        rows.append((year, pq.read_metadata(path).num_rows))
    df = pd.DataFrame(sorted(rows), columns=["publication_year", "works"])
    print(df.to_string(index=False))
    print(f"\n{len(df)} years | {df['works'].sum():,} works total")


def main():
    parser = argparse.ArgumentParser(description="Preview the Economics Parquet data.")
    parser.add_argument("year", nargs="?", type=int, help="Year to preview (e.g. 2020).")
    parser.add_argument("--rows", type=int, default=20, help="How many rows to show (default 20).")
    parser.add_argument("--cols", help="Comma-separated columns to show (default: a readable subset).")
    parser.add_argument("--search", help="Only rows whose title contains this text (case-insensitive).")
    parser.add_argument("--csv", help="Write the selected rows to this CSV path instead of printing.")
    parser.add_argument("--summary", action="store_true", help="Show works-per-year for the whole dataset.")
    args = parser.parse_args()

    if args.summary:
        show_summary()
        return
    if args.year is None:
        parser.error("give a YEAR (e.g. 'python peek.py 2020') or use --summary")

    path = year_path(args.year)
    if not path:
        parser.error(f"no data file for year {args.year} under {DATA_DIR}")

    df = pd.read_parquet(path)
    if args.search:
        df = df[df["title"].fillna("").str.contains(args.search, case=False)]

    # Choose columns: explicit --cols, else the readable default (kept to those
    # that actually exist).
    if args.cols:
        cols = [c.strip() for c in args.cols.split(",")]
    else:
        cols = [c for c in DEFAULT_COLS if c in df.columns]
    df = df[cols]

    if args.csv:
        df.to_csv(os.path.expanduser(args.csv), index=False)
        print(f"wrote {len(df):,} rows x {len(cols)} cols -> {args.csv}")
        return

    total = len(df)
    with pd.option_context("display.max_rows", args.rows,
                           "display.max_colwidth", 60,
                           "display.width", 200):
        print(df.head(args.rows).to_string(index=False))
    print(f"\nshowing {min(args.rows, total)} of {total:,} rows"
          + (f" matching '{args.search}'" if args.search else "") + f" for {args.year}")


if __name__ == "__main__":
    main()
