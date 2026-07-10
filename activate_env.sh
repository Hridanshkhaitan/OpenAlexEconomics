#!/bin/bash
# Activate the Python environment for the OpenAlex Economics project.
# Loads the arrow module (provides pyarrow) and the project virtualenv.
module load python/3.11 arrow/17.0.0
source ~/econ_env/bin/activate
echo "OpenAlex Economics environment activated."
