#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTER
Space-based Imaging Spectroscopy and Thermal PathfindER
Author: Winston Olson-Duvall
"""

import glob
import json
import os
import shutil
import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np

from osgeo import gdal
from PIL import Image



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


def convert_to_geotiff_and_png(pigment_path, basename, band_name, units, description, disclaimer):

    in_file = gdal.Open(pigment_path)

    # Temporary geotiff
    temp_file = f"work/{basename}_tmp.tif"

    # Set the output raster transform and projection properties
    driver = gdal.GetDriverByName("GTIFF")
    tiff = driver.Create(temp_file,
                         in_file.RasterXSize,
                         in_file.RasterYSize,
                         1,
                         gdal.GDT_Float32)

    tiff.SetGeoTransform(in_file.GetGeoTransform())
    tiff.SetProjection(in_file.GetProjection())

    # Dataset description
    tiff.SetMetadataItem("DESCRIPTION", disclaimer + description)

    in_band = in_file.GetRasterBand(1)

    out_band = tiff.GetRasterBand(1)
    out_band.WriteArray(in_band.ReadAsArray())
    out_band.SetDescription(band_name)
    out_band.SetNoDataValue(in_band.GetNoDataValue())
    out_band.SetMetadataItem("UNITS", units)
    out_band.SetMetadataItem("DESCRIPTION", description)

    del tiff, driver

    # Save as cloud optimized geotiff
    cog_file = f"output/{basename}.tif"
    os.system(f"gdaladdo -minsize 900 {temp_file}")
    os.system(f"gdal_translate {temp_file} {cog_file} -co COMPRESS=LZW -co TILED=YES -co COPY_SRC_OVERVIEWS=YES")

    # Convert to PNG
    pigment = in_band.ReadAsArray()
    pigment[pigment == in_band.GetNoDataValue()] = np.nan

    # Log transform for better visualization
    pigment = np.log10(pigment)

    # Clip image and normalize 0-1
    low = np.nanpercentile(pigment, 5)
    hi = np.nanpercentile(pigment, 95)
    pigment = (pigment - low) / (hi - low)

    cmap = plt.get_cmap('winter')

    qlook = cmap(pigment)[:, :, :3]
    qlook = (255 * qlook).astype(np.uint8)
    qlook[np.isnan(pigment)] = 0

    im = Image.fromarray(qlook, 'RGB')

    quicklook_file = cog_file.replace(".tif", ".png")

    im.save(quicklook_file)


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

    # Get experimental
    experimental = run_config['inputs']['experimental']
    if experimental:
        disclaimer = "(DISCLAIMER: THIS DATA IS EXPERIMENTAL AND NOT INTENDED FOR SCIENTIFIC USE) "
    else:
        disclaimer = ""

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

    corfl_basename = os.path.basename(run_config["inputs"]["corrected_reflectance_dataset"])
    frcov_basename = os.path.basename(run_config["inputs"]["fractional_cover_dataset"])
    aquapig_basename = get_aquapig_basename(corfl_basename, run_config["inputs"]["crid"])
    chla_basename = f"{aquapig_basename}_CHL"
    phyco_basename = f"{aquapig_basename}_PHYCO"

    corfl_envi_path = f"input/{corfl_basename}/{corfl_basename}.bin"
    frcov_tiff_path = f"input/{frcov_basename}/{frcov_basename}.tif"

    tmp_chla_envi_path = f"work/{corfl_basename}_aqchla"
    tmp_phyco_envi_path = f"work/{corfl_basename}_phyco"

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

    # Generate metadata
    print("Generating metadata in .met.json files")
    generate_metadata(run_config,
                      f"output/{aquapig_basename}.met.json",
                      {'product': 'AQUAPIG',
                       'processing_level': 'L2B',
                       'description': f"{disclaimer}Aquatic pigments - chlorophyll A content mg m-3, and phycocyanin "
                                      f"content (mg m-3) estimated using mixture density network."})

    chla_desc = "Chlorophyll A content mg m-3"
    generate_metadata(run_config,
                      f"output/{chla_basename}.met.json",
                      {'product': 'AQUAPIG_CHL',
                       'processing_level': 'L2B',
                       'description': disclaimer + chla_desc})

    phyco_desc = "Phycocyanin content (mg m-3) estimated using mixture density network."
    generate_metadata(run_config,
                      f"output/{phyco_basename}.met.json",
                      {'product': 'AQUAPIG_PHYCO',
                       'processing_level': 'L2B',
                       'description': disclaimer + phyco_desc})

    # Convert to geotiff and png
    print("Converting ENVI files to GeoTIFF and PNG and saving to output folder")
    convert_to_geotiff_and_png(tmp_chla_envi_path, chla_basename, "chlorophyll_a", "mg m-3", chla_desc, disclaimer)
    convert_to_geotiff_and_png(tmp_phyco_envi_path, phyco_basename, "phycocyanin", "mg m-3", phyco_desc, disclaimer)

    # Copy any remaining files to output
    print("Copying runconfig to output folder")
    shutil.copyfile("runconfig.json", f"output/{aquapig_basename}.runconfig.json")

    # If experimental, prefix filenames with "EXPERIMENTAL-"
    if experimental:
        for file in glob.glob(f"output/SISTER*"):
            shutil.move(file, f"output/EXPERIMENTAL-{os.path.basename(file)}")


if __name__ == "__main__":
    main()
