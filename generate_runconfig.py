#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTER
Space-based Imaging Spectroscopy and Thermal PathfindER
Author: Adam Chlus, Winston Olson-Duvall, Dan Yu
"""

import argparse
import json
import os
import sys


def main():
    """
        This function takes as input the path to an inputs.json file and exports a run config json
        containing the arguments needed to run the SISTER aquatic-pigments PGE.

    """

    parser = argparse.ArgumentParser(description="Parse inputs to create runconfig.json")
    parser.add_argument("--corrected_reflectance_dataset", help="Path to reflectance dataset")
    parser.add_argument("--fractional_cover_dataset", help="Path to uncertainty dataset")
    parser.add_argument("--crid", help="CRID value")
    parser.add_argument("--experimental", help="If true then designates data as experiemntal")
    args = parser.parse_args()

    run_config = {
        "inputs": {
            "corrected_reflectance_dataset": args.corrected_reflectance_dataset,
            "fractional_cover_dataset": args.fractional_cover_dataset,
            "crid": args.crid,
        }
    }
    run_config["inputs"]["experimental"] = True if args.experimental.lower() == "true" else False

    # Add metadata to runconfig
    corfl_basename = os.path.basename(run_config["inputs"]["corrected_reflectance_dataset"])

    stac_json_path = os.path.join(run_config["inputs"]["corrected_reflectance_dataset"], f"{corfl_basename}.json")
    with open(stac_json_path, "r") as f:
        stac_item = json.load(f)
    run_config["metadata"] = stac_item["properties"]
    run_config["metadata"]["geometry"] = stac_item["geometry"]

    # Write out runconfig.json
    config_file = "runconfig.json"
    with open(config_file, "w") as outfile:
        json.dump(run_config, outfile, indent=4)


if __name__ == "__main__":
    main()
