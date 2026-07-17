"""
Build the Parquet dataset from the OpenAlex archives.

Each record keeps every field that was downloaded. Seventeen commonly used fields
are extracted into typed, analysis-ready columns; every other raw top-level field
is stored whole as one JSON-text column (authorships, topics, referenced_works,
and so on are not flattened). A final `extra_json` column captures any field not
listed below, so nothing is ever dropped.

Output is one file per year, grouped by century, matching the archive layout:

    <out-dir>/2000s/2020.parquet

Read the whole dataset, or any slice, with a single call:

    df = pd.read_parquet("<out-dir>")
    df = pd.read_parquet("<out-dir>", filters=[("publication_year", ">=", 2000)])
    authors = json.loads(df.iloc[0]["authorships"])   # nested fields are JSON text

The build streams each year in row batches so memory stays bounded, and writes
every file against one fixed schema so the whole dataset reads back cleanly.

Usage:
    python build_parquet.py \
        --archive-dir /project/def-kmcel/hridansh/openalex_econ/data/archive \
        --out-dir     /scratch/hridansh/openalex_econ_download/parquet
"""

import argparse
import glob
import gzip
import json
import os
import re

import pyarrow as pa
import pyarrow.parquet as pq

BATCH_ROWS = 20000   # rows buffered before each Parquet write

# Seventeen curated, typed columns.
CURATED_SCHEMA = [
    ("id", pa.string()),
    ("doi", pa.string()),
    ("title", pa.string()),
    ("publication_year", pa.int32()),
    ("publication_date", pa.string()),
    ("type", pa.string()),
    ("language", pa.string()),
    ("cited_by_count", pa.int64()),
    ("field", pa.string()),
    ("subfield", pa.string()),
    ("primary_topic", pa.string()),
    ("author_count", pa.int32()),
    ("first_author", pa.string()),
    ("journal", pa.string()),
    ("is_oa", pa.bool_()),
    ("referenced_works_count", pa.int64()),
    ("abstract", pa.string()),
]

# Raw top-level fields kept whole, each as one JSON-text column. The raw
# `primary_topic` object is stored as `primary_topic_json` so it does not clash
# with the curated `primary_topic` display-name string above.
RAW_FIELDS = [
    "abstract_inverted_index", "apc_list", "apc_paid", "authorships", "awards",
    "best_oa_location", "biblio", "citation_normalized_percentile",
    "cited_by_percentile_year", "concepts", "content_urls",
    "corresponding_author_ids", "corresponding_institution_ids",
    "countries_distinct_count", "counts_by_year", "created_date", "display_name",
    "funders", "fwci", "has_content", "has_fulltext", "ids", "indexed_in",
    "institutions", "institutions_distinct_count", "is_paratext", "is_retracted",
    "is_xpac", "keywords", "locations", "locations_count", "mesh", "open_access",
    "primary_location", "primary_topic_json", "referenced_works", "related_works",
    "sustainable_development_goals", "topics", "updated_date",
]

# Raw fields already represented by a curated column above; not duplicated. The
# full OpenAlex id URL still survives inside the `ids` column.
CURATED_RAW_KEYS = {
    "id", "doi", "title", "publication_year", "publication_date", "type",
    "language", "cited_by_count", "referenced_works_count",
}

SCHEMA = pa.schema(
    [pa.field(name, dtype) for name, dtype in CURATED_SCHEMA]
    + [pa.field(name, pa.string()) for name in RAW_FIELDS]
    + [pa.field("extra_json", pa.string())]
)
RAW_FIELD_SET = set(RAW_FIELDS)


def reconstruct_abstract(inverted_index):
    """Rebuild abstract text from OpenAlex's {word: [positions]} inverted index."""
    if not inverted_index:
        return None
    positions = [(i, word) for word, idxs in inverted_index.items() for i in idxs]
    positions.sort()
    return " ".join(word for _, word in positions)


def curated_columns(work):
    """Return the seventeen curated, typed columns for one work."""
    topic = work.get("primary_topic") or {}
    source = (work.get("primary_location") or {}).get("source") or {}
    authorships = work.get("authorships") or []
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
        "is_oa": (work.get("open_access") or {}).get("is_oa"),
        "referenced_works_count": len(work.get("referenced_works") or []),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
    }


def build_row(work):
    """Build one output row: curated columns plus every raw field as JSON text."""
    row = curated_columns(work)
    extra = {}
    for key, value in work.items():
        if key in CURATED_RAW_KEYS:
            continue
        column = "primary_topic_json" if key == "primary_topic" else key
        text = value if (value is None or isinstance(value, str)) else json.dumps(value, ensure_ascii=False)
        if column in RAW_FIELD_SET:
            row[column] = text
        else:
            extra[key] = value
    row["extra_json"] = json.dumps(extra, ensure_ascii=False) if extra else None
    return row


def build_year(archive_path, out_dir):
    """Stream one archive file into one Parquet file under its century folder."""
    year = re.search(r"econ_(\d+)\.jsonl\.gz$", os.path.basename(archive_path)).group(1)
    century_dir = os.path.join(out_dir, f"{int(year) // 100 * 100}s")
    os.makedirs(century_dir, exist_ok=True)
    out_path = os.path.join(century_dir, f"{year}.parquet")

    writer = None
    batch = []
    total = 0
    with gzip.open(archive_path, "rt", encoding="utf-8") as f:
        for line in f:
            batch.append(build_row(json.loads(line)))
            total += 1
            if len(batch) >= BATCH_ROWS:
                if writer is None:
                    writer = pq.ParquetWriter(out_path, SCHEMA, compression="zstd")
                writer.write_table(pa.Table.from_pylist(batch, schema=SCHEMA))
                batch = []

    if total == 0:
        print(f"{os.path.basename(archive_path)}: 0 rows (skipped)")
        return
    if writer is None:
        writer = pq.ParquetWriter(out_path, SCHEMA, compression="zstd")
    if batch:
        writer.write_table(pa.Table.from_pylist(batch, schema=SCHEMA))
    writer.close()
    print(f"{os.path.basename(archive_path)}: {total} rows -> {out_path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Build the OpenAlex Economics Parquet dataset.")
    parser.add_argument("--archive-dir", required=True, help="Directory tree of econ_<year>.jsonl.gz files.")
    parser.add_argument("--out-dir", required=True, help="Output directory for the Parquet dataset.")
    args = parser.parse_args()

    archives = sorted(glob.glob(os.path.join(args.archive_dir, "**", "econ_*.jsonl.gz"), recursive=True))
    for archive_path in archives:
        build_year(archive_path, args.out_dir)


if __name__ == "__main__":
    main()
