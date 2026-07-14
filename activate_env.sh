#!/bin/bash
# Activate the Python environment for the OpenAlex Economics project.
#
# The virtualenv lives on /project (not /home) so the pipeline keeps working
# even when the /home filesystem has problems. The OpenAlex API key is read
# from a private file on /project and exported for extract_econ.py.
module load python/3.11 arrow/17.0.0
source /project/def-kmcel/hridansh/econ_env/bin/activate
KEY_FILE=/project/def-kmcel/hridansh/openalex_api_key
if [ -f "$KEY_FILE" ]; then
    export OPENALEX_API_KEY=$(cat "$KEY_FILE")
    echo "OpenAlex Economics environment activated (API key loaded)."
else
    echo "OpenAlex Economics environment activated (WARNING: no API key at $KEY_FILE)."
fi
