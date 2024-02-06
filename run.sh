#!/bin/bash

# Use aquatic-pigments conda env from docker image
source activate ap-chla

# Get repository directory
REPO_DIR=$(cd "$(dirname "$0")"; pwd -P)

# Generate runconfig
python ${REPO_DIR}/generate_runconfig.py "${@:1}"

# Execute aquatic-pigments
python ${REPO_DIR}/sister_aquatic_pigments.py runconfig.json
