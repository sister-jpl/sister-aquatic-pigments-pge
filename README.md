# SISTER Aquatic Pigments PGE Documentation

## Description

The sister-aquatic-pigments-pge repository is a wrapper for two aquatic pigment estimation repositories:
* [Chlorophyll A](https://github.com/EnSpec/sister-mdn_chlorophyll)
* [Phycocyanin](https://github.com/EnSpec/sister-mdn_phycocyanin)

## PGE Arguments

The sister-aquatic-pigments-pge PGE takes the following arguments:


| Argument                      | Type                                 | Description                                        | Default |
|-------------------------------|--------------------------------------|----------------------------------------------------|---------|
| corrected_reflectance_dataset | file                                 | S3 URL to the corrected reflectance dataset folder | -       |
| fractional_cover_dataset      | file                                 | S3 URL to the fractional cover dataset folder      | -       |
| crid                          | config                               | Composite Release ID to tag file names             | 000     |
| experimental                  | Designates outputs as "experimental" | 'True'                                             |

## Outputs

The L2B aquatic pigments PGE outputs Cloud-Optimized GeoTIFFs (COGs) and associated metadata and ancillary files. The 
outputs of the PGE use the following naming convention:

    (EXPERIMENTAL-)SISTER_INSTRUMENT_LEVEL_PRODUCT_YYYYMMDDTHHMMSS_CRID(_ANCILLARY).EXTENSION

where `(_ANCILLARY)` is optional and is used to identify ancillary products, and the "EXPERIMENTAL-" prefix is also 
optional and is only added when the "experimental" flag is set to True.

The following data products are produced:

| Product                                 | Format, Units                   | Example filename                                           |
|-----------------------------------------|---------------------------------|------------------------------------------------------------|
| Chlorophyll A concentration             | Cloud-Optimized GeoTIFF, mg m-3 | SISTER_AVCL_L2B_AQUAPIG_20180126T204322_000_CHL.tif        |
| Chlorophyll A metadata (STAC formatted) | JSON                            | SISTER_AVCL_L2B_AQUAPIG_20180126T204322_000_CHL.json       |
| Chlorophyll A browse image              | PNG                             | SISTER_AVCL_L2B_AQUAPIG_20180126T204322_000_CHL.png        |
| Phycocyanin concentration               | Cloud-Optimized GeoTIFF, mg m-3 | SISTER_AVCL_L2B_AQUAPIG_20180126T204322_000_PHYCO.tif      |
| Phycocyanin metadata (STAC formatted)   | JSON                            | SISTER_AVCL_L2B_AQUAPIG_20180126T204322_000_PHYCO.json     |
| Phycocyanin browse image                | PNG                             | SISTER_AVCL_L2B_AQUAPIG_20180126T204322_000_PHYCO.png      |
| PGE metadata (STAC formatted)           | JSON                            | SISTER_AVCL_L2B_AQUAPIG_20180126T204322_000.json           |
| PGE log file                            | Text                            | SISTER_AVCL_L2B_AQUAPIG_20180126T204322_000.log            |
| PGE run config                          | JSON                            | SISTER_AVCL_L2B_AQUAPIG_20180126T204322_000.runconfig.json |

Metadata files are [STAC formatted](https://stacspec.org/en) and compatible with tools in the [STAC ecosystem](https://stacindex.org/ecosystem).

## Executing the Algorithm

This algorithm requires [Anaconda Python](https://www.anaconda.com/download)

To install and run the code, first clone the repository and execute the install script:

    git clone https://github.com/sister-jpl/sister-aquatic-pigments-pge.git
    cd sister-aquatic-pigments-pge
    ./install.sh
    cd ..

Then, create a working directory and enter it:

    mkdir WORK_DIR
    cd WORK_DIR

Copy input files to the work directory. For each "dataset" input, create a folder with the dataset name, then download 
the data file(s) and STAC JSON file into the folder.  For example, the reflectance dataset input would look like this:

    WORK_DIR/SISTER_AVCL_L2A_CORFL_20180126T204322_000/SISTER_AVCL_L2A_CORFL_20180126T204322_000.bin
    WORK_DIR/SISTER_AVCL_L2A_CORFL_20180126T204322_000/SISTER_AVCL_L2A_CORFL_20180126T204322_000.hdr
    WORK_DIR/SISTER_AVCL_L2A_CORFL_20180126T204322_000/SISTER_AVCL_L2A_CORFL_20180126T204322_000.json

Finally, run the code 

    ../sister-aquatic-pigments-pge/run.sh --corrected_reflectance_dataset SISTER_AVCL_L2A_CORFL_20180126T204322_000 --fractional_cover_dataset SISTER_AVCL_L2B_FRCOV_20180126T204322_000
