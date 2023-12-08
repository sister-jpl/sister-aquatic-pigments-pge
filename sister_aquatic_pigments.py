#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTER
Space-based Imaging Spectroscopy and Thermal PathfindER
Author: Winston Olson-Duvall
"""

import datetime as dt
import glob
import json
import os
import shutil
import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
import pystac

from osgeo import gdal
from PIL import Image


def get_aquapig_basename(corfl_basename, crid):
    # Replace product type
    tmp_basename = corfl_basename.replace("L2A_CORFL", "L2B_AQUAPIG")
    # Split, remove old CRID, and add new one
    tokens = tmp_basename.split("_")[:-1] + [str(crid)]
    return "_".join(tokens)


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


def generate_stac_metadata(basename, description, in_meta):

    out_meta = {}
    out_meta['id'] = basename
    out_meta['start_datetime'] = dt.datetime.strptime(in_meta['start_time'], "%Y-%m-%dT%H:%M:%SZ")
    out_meta['end_datetime'] = dt.datetime.strptime(in_meta['end_time'], "%Y-%m-%dT%H:%M:%SZ")
    # Split corner coordinates string into list
    geometry = in_meta['bounding_box']
    # Add first coord to the end of the list to close the polygon
    geometry.append(geometry[0])
    out_meta['geometry'] = geometry
    product = basename.split('_')[3]
    if "CHL" in basename:
        product += "_CHL"
    elif "PHYCO" in basename:
        product += "_PHYCO"
    out_meta['properties'] = {
        'sensor': in_meta['sensor'],
        'description': description,
        'product': product,
        'processing_level': basename.split('_')[2]
    }
    return out_meta


def create_item(metadata, assets):
    item = pystac.Item(
        id=metadata['id'],
        datetime=metadata['start_datetime'],
        start_datetime=metadata['start_datetime'],
        end_datetime=metadata['end_datetime'],
        geometry=metadata['geometry'],
        bbox=None,
        properties=metadata['properties']
    )
    # Add assets
    for key, href in assets.items():
        item.add_asset(key=key, asset=pystac.Asset(href=href))
    return item


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

    chla_desc = "Chlorophyll A content mg m-3"
    phyco_desc = "Phycocyanin content (mg m-3) estimated using mixture density network."

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

    # Update the path variables if now experimental
    log_path = glob.glob("output/*%s.log" % run_config['inputs']['crid'])[0]
    out_runconfig_path = log_path.replace(".log", ".runconfig.json")
    aquapig_basename = os.path.basename(log_path)[:-4]

    # Generate STAC
    catalog = pystac.Catalog(id=corfl_basename,
                             description=f'{disclaimer}This catalog contains the output data products of the SISTER '
                                         f'aquatic pigments PGE, including chlorophyll A and phycocyanin in '
                                         f'cloud-optimized GeoTIFF format. Execution artifacts including the '
                                         f'runconfig file and execution log file are also included.')

    # Add an item for the top level to hold runconfig and log
    description = f"{disclaimer}Aquatic pigments - chlorophyll A content mg m-3, and phycocyanin content (mg m-3) " \
                  f"estimated using mixture density network."
    metadata = generate_stac_metadata(aquapig_basename, description, run_config["metadata"])
    assets = {
        "runconfig": f"./{os.path.basename(out_runconfig_path)}",
        "log": f"./{os.path.basename(log_path)}",
    }
    item = create_item(metadata, assets)
    catalog.add_item(item)

    # Add items for data products
    tif_files = glob.glob("output/*SISTER*.tif")
    tif_files.sort()
    for tif_file in tif_files:
        tif_basename = os.path.basename(tif_file)[:-4]
        if "CHL" in tif_basename:
            description = disclaimer + chla_desc
        elif "PHYCO" in tif_basename:
            description = disclaimer +phyco_desc
        metadata = generate_stac_metadata(tif_basename, description, run_config["metadata"])
        assets = {
            "cog": f"./{os.path.basename(tif_file)}",
            "browse": f"./{os.path.basename(tif_file).replace('.tif', '.png')}",
        }
        item = create_item(metadata, assets)
        catalog.add_item(item)

    # set catalog hrefs
    catalog.normalize_hrefs(f"./output/{aquapig_basename}")

    # save the catalog
    catalog.describe()
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    print("Catalog HREF: ", catalog.get_self_href())

    # Move the assets from the output directory to the stac item directories
    for item in catalog.get_items():
        for asset in item.assets.values():
            fname = os.path.basename(asset.href)
            shutil.move(f"output/{fname}", f"output/{aquapig_basename}/{item.id}/{fname}")


if __name__ == "__main__":
    main()
