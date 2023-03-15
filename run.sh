#!/bin/bash

# Use aquatic-pigments conda env from docker image
source activate aquatic-pigments

# Get repository directory
REPO_DIR=$(cd "$(dirname "$0")"; pwd -P)

# Generate runconfig
python ${REPO_DIR}/generate_runconfig.py inputs.json

# Execute isofit
python ${REPO_DIR}/sister_aquatic_pigments.py runconfig.json