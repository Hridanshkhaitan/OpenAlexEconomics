"""
Build the FULL-FIDELITY Parquet dataset from the OpenAlex archives.

Every field present in the raw archive is retained, so a shared Parquet file can
never be missing data that was downloaded. The 17 curated, analysis-ready columns
from the original build are kept exactly (typed, easy to query); every remaining
raw top-level field is added as its own column, with nested structures
(authorships, topics, referenced_works, locations, ...) stored WHOLE as one
JSON-text column rather than flattened.

Column groups (in this order):
  1. 17 curated/typed columns: id, doi, title, publication_year, publication_date,
     type, language, cited_by_count, field, subfield, primary_topic, author_count,
     first_author, journal, is_oa, referenced_works_count, abstract.
  2. One column per remaining raw top-level field. Objects/arrays are stored as
     JSON text; raw scalars are stored as JSON text too, so every raw column has a
     single uniform string type across all years (clean directory reads). The raw
     primary_topic object is kept as `primary_topic_json` (the curated
     `primary_topic` string display-name stays in group 1).
  3. `extra_json`: any raw field not seen during the schema scan (future-proofing);
     normally empty.

Raw scalar fields that merely duplicate a curated column (id, doi, title,
publication_year, publication_date, type, language, cited_by_count,
referenced_works_count) are not repeated -- the curated column already carries
them, and the full OpenAlex id URL also survives inside the `ids` column.

Layout is unchanged: <out-dir>/<century>s/<year>.parquet, read with a single
pd.read_parquet(dir). The build streams in batches so memory stays bounded even
for the largest years, and writes every file with one fixed schema so the whole
dataset reads back without schema-unification errors.

Usage:
    python build_parquet_full.py \
        --archive-dir /project/def-kmcel/hridansh/openalex_econ/data/archive \
        --out-dir     /scratch/hridansh/openalex_econ_download/parquet_full
"""

import argparse
import glob
import gzip
import json
import os
import re

import pyarrow as pa
import pyarrow.parquet as pq

BATCH_ROWS = 20000   # rows buffered in memory before each Parquet write

# Raw top-level fields that already have an equivalent curated column; not repeated.
SKIP_RAW = {
    "id", "doi", "title", "publication_year", "publication_date", "type",
    "language", "cited_by_count", "referenced_works_count",
}

# The 17 curated columns, with their Arrow types (group 1, always present).
CURATED_FIELDS = [
    ("id", pa.string()), ("doi", pa.string()), ("title", pa.string()),
    ("publication_year", pa.int32()), ("publication_date", pa.string()),
    ("type", pa.string()), ("language", pa.string()),
    ("cited_by_count", pa.int64()), ("field", pa.string()),
    ("subfield", pa.string()), ("primary_topic", pa.string()),
    ("author_count", pa.int32()), ("first_author", pa.string()),
    ("journal", pa.string()), ("is_oa", pa.bool_()),
    ("referenced_works_count", pa.int64()), ("abstract", pa.string()),
]


def reconstruct_abstract(inverted_index):
    """Rebuild abstract text from OpenAlex's inverted-index representation."""
    if not inverted_index:
        return None
    positions = []
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(word for _, word in positions)


def extract_curated(work):
    """Return the 17 curated, typed columns for one work (unchanged from before)."""
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


def raw_col_name(key):
    """Column name a raw field is stored under (primary_topic -> primary_topic_json)."""
    return "primary_topic_json" if key == "primary_topic" else key


def scan_raw_keys(archives):
    """Pass 1: union of every raw top-level field across the whole corpus.

    Reading all records once guarantees the schema has a dedicated column for
    every field that occurs anywhere, so nothing lands in extra_json in practice.
    """
    keys = set()
    for path in archives:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                for k in json.loads(line).keys():
                    if k not in SKIP_RAW:
                        keys.add(raw_col_name(k))
    return sorted(keys)


def build_schema(raw_keys):
    """Assemble the single fixed Arrow schema used for every output file."""
    fields = [pa.field(n, t) for n, t in CURATED_FIELDS]
    fields += [pa.field(k, pa.string()) for k in raw_keys]   # raw fields: JSON text
    fields += [pa.field("extra_json", pa.string())]
    return pa.schema(fields)


def build_row(work, raw_key_set):
    """Build one output row: curated columns + every raw field as JSON text."""
    row = extract_curated(work)
    extra = {}
    for k, v in work.items():
        if k in SKIP_RAW:
            continue
        col = raw_col_name(k)
        value = v if (v is None or isinstance(v, str)) else json.dumps(v, ensure_ascii=False)
        if col in raw_key_set:
            row[col] = value
        else:
            extra[k] = v   # a field the scan did not see; keep it, do not lose it
    row["extra_json"] = json.dumps(extra, ensure_ascii=False) if extra else None
    return row


def build_year(archive_path, out_dir, schema, raw_key_set):
    """Stream one archive into one Parquet file under its century folder."""
    year = re.search(r"econ_(\d+)\.jsonl\.gz$", os.path.basename(archive_path)).group(1)
    century_dir = os.path.join(out_dir, f"{int(year) // 100 * 100}s")
    os.makedirs(century_dir, exist_ok=True)
    out_path = os.path.join(century_dir, f"{year}.parquet")

    writer = None
    batch = []
    total = 0

    def flush():
        nonlocal batch
        if not batch:
            return
        table = pa.Table.from_pylist(batch, schema=schema)
        writer.write_table(table)
        batch = []

    with gzip.open(archive_path, "rt", encoding="utf-8") as f:
        for line in f:
            batch.append(build_row(json.loads(line), raw_key_set))
            total += 1
            if len(batch) >= BATCH_ROWS:
                if writer is None:
                    writer = pq.ParquetWriter(out_path, schema, compression="zstd")
                flush()

    if total == 0:
        print(f"{os.path.basename(archive_path)}: 0 rows (skipped)")
        return
    if writer is None:
        writer = pq.ParquetWriter(out_path, schema, compression="zstd")
    flush()
    writer.close()
    print(f"{os.path.basename(archive_path)}: {total} rows -> {out_path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Build full-fidelity Parquet from OpenAlex archives.")
    parser.add_argument("--archive-dir", required=True, help="Directory tree of econ_<year>.jsonl.gz files.")
    parser.add_argument("--out-dir", required=True, help="Output directory for the Parquet dataset.")
    args = parser.parse_args()

    archives = sorted(glob.glob(os.path.join(args.archive_dir, "**", "econ_*.jsonl.gz"), recursive=True))
    if not archives:
        print(f"No archive files found under {args.archive_dir}")
        return

    print(f"pass 1/2: scanning {len(archives)} archives for the full field set ...", flush=True)
    raw_keys = scan_raw_keys(archives)
    schema = build_schema(raw_keys)
    raw_key_set = set(raw_keys)
    print(f"schema has {len(schema.names)} columns "
          f"(17 curated + {len(raw_keys)} raw + extra_json)", flush=True)
    print("  raw columns: " + ", ".join(raw_keys), flush=True)

    print("pass 2/2: building Parquet files ...", flush=True)
    for archive_path in archives:
        build_year(archive_path, args.out_dir, schema, raw_key_set)
    print("done.", flush=True)


if __name__ == "__main__":
    main()
