# OpenAlex Economics

Bibliometrics project on OpenAlex works in the field of Economics.

## Layout
- `py_code/` — pipeline and analysis code
- `data/` — datasets (Narval only, gitignored; lives at `/project/def-kmcel/hridansh/openalex_econ/data/`)
- `logs/` — SLURM and run logs (gitignored)

Bulk downloads/processing happen in `/scratch/hridansh/openalex_econ_download` (purged after 60 days), with kept outputs moved to `data/`.
