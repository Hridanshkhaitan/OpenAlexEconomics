#!/bin/bash
# SLURM job: build the full-fidelity Parquet dataset on a compute node.
#
# The build only reads local archive files (no internet), so it runs fine on an
# air-gapped compute node -- which, unlike a login node, has the memory and CPU
# budget for serializing every raw field. Submit with:
#     sbatch scripts/build_full.sh
#
#SBATCH --account=def-kmcel
#SBATCH --job-name=econ_parquet_full
#SBATCH --time=3:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=1
#SBATCH --output=/scratch/hridansh/openalex_econ_download/logs/build_full_%j.log

set -euo pipefail

module load python/3.11 arrow/17.0.0
source /project/def-kmcel/hridansh/econ_env/bin/activate

python /project/def-kmcel/hridansh/openalex_econ/py_code/build_parquet.py \
    --archive-dir /project/def-kmcel/hridansh/openalex_econ/data/archive \
    --out-dir     /scratch/hridansh/openalex_econ_download/parquet_full

echo "SLURM build finished at $(date)"
