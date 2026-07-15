# EDA query scripts

These are the exact scripts used to produce `eda_report.txt` and the figures. Each
is a standalone Python script that queries the Parquet dataset with DuckDB and
prints its results to stdout. Nothing here modifies the data — all read-only.

## How to run

On Narval (where the data lives):

```bash
source /project/def-kmcel/hridansh/openalex_econ/activate_env.sh
python analysis/eda/queries/temporal/temporal_main.py
```

Every script points at the dataset via one line near the top:

```python
P = "/project/def-kmcel/hridansh/openalex_econ/data/parquet/**/*.parquet"
```

Change that path if you move the data. Requirements: `duckdb`, `pandas`,
`matplotlib` (all already in the project venv activated above).

## Layout — one folder per analysis dimension (matches the report sections)

| Folder | Report section | What it computes |
|---|---|---|
| `temporal/` | 3. Temporal Patterns | works per decade/year, growth rates, peak/plateau, war-era dips, team-size & citation-aging over time, pre-1900 character |
| `completeness/` | 4. Missingness & Coverage | null/empty audit of every column, coverage by decade, date consistency, and the raw-archive field inventory (49 vs 17 fields) |
| `citations/` | 5. Citations | distribution, zero-cited shares, concentration (top 1%), most-cited works, references, team-size vs citations |
| `venues/` | 6. Venues | journal null rate, diversity/concentration, top venues, repository/eBook heuristics, name-variant duplicates, medical leakage |
| `content/` | 7. Content Quality | language & type distributions, duplicate/furniture titles, abstract coverage & the publisher-selection bias |
| `classification/` | 8. Topic Classification | subfield/topic structure, non-econ leakage estimate, filtering strategies |
| `authors/` | 9. Authors | author-count distribution, zero-author works, solo-authorship decline, name-format inconsistency, placeholder authors |

Within each folder:
- `*_main.py` — the primary analysis for that dimension.
- `*_followup.py` — deeper dives chasing a surprise found in the main run.
- `*_verify*.py` / `verifier_*` — adversarial re-computations that independently
  re-ran each headline number against the full corpus (this is what caught and
  corrected the 2020s zero-reference figure noted in the report).

At the root:
- `00_initial_probe.py` — first schema/scale sanity check.
- `make_figures.py` — regenerates all 11 PNGs and `works_per_year.txt`.

## Note on provenance

These scripts are preserved verbatim as they were run — including the iterative
`followup`/`verify` scripts — so the analysis is fully reproducible and auditable,
not just the final numbers. They were written to explore, so naming and style
vary between them; `make_figures.py` is the most polished (it is the deliverable
that renders the charts).
