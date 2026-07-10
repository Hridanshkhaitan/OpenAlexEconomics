# OpenAlex Economics

Bibliometrics project on OpenAlex works in the field of Economics.

## Layout
- `py_code/` — pipeline and analysis code
- `data/` — datasets (Narval only, gitignored)
- `logs/` — SLURM and run logs (gitignored)

Bulk downloads/processing happen in `/scratch/hridansh/openalex_econ_download` (purged after 60 days), with kept outputs moved to `data/`.
