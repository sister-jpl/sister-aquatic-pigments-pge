#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTER
Space-based Imaging Spectroscopy and Thermal PathfindER
Author: Winston Olson-Duvall
"""

import json
import os
import subprocess
import sys


def get_aquapig_basename(corfl_basename, crid):
    # Replace product type
    tmp_basename = corfl_basename.replace("L2A_CORFL", "L2B_AQUAPIG")
    # Split, remove old CRID, and add new one
    tokens = tmp_basename.split("_")[:-1] + [str(crid)]
    return "_".join(tokens)


def generate_metadata(run_config, json_path, new_metadata):

    metadata = run_config['metadata']
    for key, value in new_metadata.items():
        metadata[key] = value
    with open(json_path, 'w') as out_obj:
        json.dump(metadata, out_obj, indent=4)


def main():
    """
        This function takes as input the path to an inputs.json file and exports a run config json
        containing the arguments needed to run the SISTER ISOFIT PGE.

    """
    in_file = sys.argv[1]

    # Read in runconfig
    print("Reading in runconfig")
    with open(in_file, "r") as f:
        run_config = json.load(f)

    # Make work dir
    print("Making work directory")
    if not os.path.exists("work"):
        subprocess.run("mkdir work", shell=True)

    # Make output dir
    print("Making output directory")
    if not os.path.exists("output"):
        subprocess.run("mkdir output", shell=True)

    # Define paths and variables
    sister_aqua_pig_dir = os.path.abspath(os.path.dirname(__file__))
    mdn_chla_dir = os.path.join(os.path.dirname(sister_aqua_pig_dir), "sister-mdn_chlorophyll")
    mdn_phyco_dir = os.path.join(os.path.dirname(sister_aqua_pig_dir), "sister-mdn_phycocyanin")

    corfl_basename = None
    frcov_basename = None
    for file in run_config["inputs"]["file"]:
        if "corrected_reflectance_dataset" in file:
            corfl_basename = os.path.basename(file["corrected_reflectance_dataset"])
        if "fractional_cover_dataset" in file:
            frcov_basename = os.path.basename(file["fractional_cover_dataset"])
    aquapig_basename = get_aquapig_basename(corfl_basename, run_config["inputs"]["config"]["crid"])
    chla_basename = f"{aquapig_basename}_CHL"
    phyco_basename = f"{aquapig_basename}_PHYCO"

    corfl_envi_path = f"input/{corfl_basename}/{corfl_basename}.bin"
    frcov_tiff_path = f"input/{frcov_basename}/{frcov_basename}.tif"

    tmp_chla_envi_name = f"{corfl_basename}_aqchla"
    tmp_chla_hdr_name = f"{corfl_basename}_aqchla.hdr"
    tmp_phyco_envi_name = f"{corfl_basename}_phyco"
    tmp_phyco_hdr_name = f"{corfl_basename}_phyco.hdr"

    log_path = f"output/{aquapig_basename}.log"

    # Run chlorophyll-a
    chla_exe = f"{mdn_chla_dir}/run_mdn.py"
    chla_cmd = [
        "conda",
        "run",
        "-n",
        "ap-chla",
        "python",
        chla_exe,
        corfl_envi_path,
        frcov_tiff_path,
        "work",
        ">>",
        log_path
    ]
    print("Running chla command: " + " ".join(chla_cmd))
    subprocess.run(" ".join(chla_cmd), shell=True)

    # Run phycocyanin
    phyco_exe = f"{mdn_phyco_dir}/run_mdn.py"
    phyco_cmd = [
        "conda",
        "run",
        "-n",
        "ap-phyco",
        "python",
        phyco_exe,
        corfl_envi_path,
        frcov_tiff_path,
        "work",
        ">>",
        log_path
    ]
    print("Running phyco command: " + " ".join(phyco_cmd))
    subprocess.run(" ".join(phyco_cmd), shell=True)

    generate_metadata(run_config,
                      f"output/{aquapig_basename}.met.json",
                      {'product': 'AQUAPIG',
                       'processing_level': 'L2B',
                       'description': "Aquatic pigments - chlorophyll A content mg-m3, and phycocyanin content (mg-m3) "
                                      "estimated using mixture density network."})

    generate_metadata(run_config,
                      f"output/{chla_basename}.met.json",
                      {'product': 'AQUAPIG_CHL',
                       'processing_level': 'L2B',
                       'description': "Chlorophyll A content mg-m3"})

    generate_metadata(run_config,
                      f"output/{phyco_basename}.met.json",
                      {'product': 'AQUAPIG_PHYCO',
                       'processing_level': 'L2B',
                       'description': "Phycocyanin content (mg-m3) estimated using mixture density network."})


if __name__ == "__main__":
    main()
