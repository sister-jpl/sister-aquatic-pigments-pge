# SISTER Aquatic Pigments PGE Documentation

## Description

The sister-aquatic-pigments-pge repository is a wrapper for two aquatic pigment estimation repositories:
* [Chlorophyll A](https://github.com/EnSpec/sister-mdn_chlorophyll)
* [Phycocyanin](https://github.com/EnSpec/sister-mdn_phycocyanin)

## Dependencies

This repository is built to run on SISTER (Space-based Imaging Spectroscopy and Thermal pathfindER), a data 
processing back-end that allows for the registration of algorithms as executable containers and execution of those 
containers at scale.  The manifest file that configures this repository for registration and describes all of its 
necessary dependencies is called `algorithm_config.yaml`.  In this file you will find:

* The repository URL and version to register
* The base Docker image which this repository gets installed into, and a reference to its Dockerfile
* The build script which is used to install this repository into the base Docker image

Specific dependencies for executing the code in this repository can be found in both the Dockerfile and the build 
script.

In addition to the above dependencies, you will need access to the MAAP API via the maap-py library in order to 
register algorithms and submit jobs.  maap-py can be obtained by running:

    git clone --single-branch --branch sister-dev https://gitlab.com/geospec/maap-py.git

## PGE Arguments

The sister-aquatic-pigments-pge PGE takes the following arguments:


| Argument                      | Type   | Description                                        | Default |
|-------------------------------|--------|----------------------------------------------------|---------|
| corrected_reflectance_dataset | file   | S3 URL to the corrected reflectance dataset folder | -       |
| fractional_cover_dataset      | file   | S3 URL to the fractional cover dataset folder      | -       |
| crid                          | config | Composite Release ID to tag file names             | 000     |

## Outputs

The L2B aquatic pigments PGE outputs Cloud-Optimized GeoTIFFs (COGs) and associated metadata and ancillary files. The 
outputs of the PGE use the following naming convention:

    SISTER_INSTRUMENT_LEVEL_PRODUCT_YYYYMMDDTHHMMSS_CRID(_ANCILLARY).EXTENSION

where `(_ANCILLARY)` is optional and is used to identify ancillary products.

| Product                     | Format, Units                   | Example filename                                           |
|-----------------------------|---------------------------------|------------------------------------------------------------|
| Chlorophyll A concentration | Cloud-Optimized GeoTIFF, mg m-3 | SISTER_AVNG_L2B_AQUAPIG_20210604T090303_000_CHL.tif        |
| Chlorophyll A metadata      | JSON                            | SISTER_AVNG_L2B_AQUAPIG_20210604T090303_000_CHL.met.json   |
| Chlorophyll A browse image  | PNG                             | SISTER_AVNG_L2B_AQUAPIG_20210604T090303_000_CHL.png        |
| Phycocyanin concentration   | Cloud-Optimized GeoTIFF, mg m-3 | SISTER_AVNG_L2B_AQUAPIG_20210604T090303_000_PHYCO.tif      |
| Phycocyanin metadata        | JSON                            | SISTER_AVNG_L2B_AQUAPIG_20210604T090303_000_PHYCO.met.json |
| Phycocyanin browse image    | PNG                             | SISTER_AVNG_L2B_AQUAPIG_20210604T090303_000_PHYCO.png      |
| PGE metadata                | JSON                            | SISTER_AVNG_L2B_AQUAPIG_20210604T090303_000.met.json       |
| PGE log file                | Text                            | SISTER_AVNG_L2B_AQUAPIG_20210604T090303_000.log            |
| PGE run config              | JSON                            | SISTER_AVNG_L2B_AQUAPIG_20210604T090303_000.runconfig.json |

## Registering the Repository with SISTER

    from maap.maap import MAAP
    
    maap = MAAP(maap_host="34.216.77.111")
    
    algo_config_path = "sister-aquatic-pigments-pge/algorithm_config.yaml"
    response = maap.register_algorithm_from_yaml_file(file_path=algo_config_path)
    print(response.text)

## Submitting a Job on SISTER

    from maap.maap import MAAP
    
    maap = MAAP(maap_host="34.216.77.111")
    
    response = maap.submitJob(
        algo_id="sister-aquatic-pigments-pge",
        version="1.0.0",
        corrected_reflectance_dataset="s3://s3.us-west-2.amazonaws.com:80/sister-ops-workspace/LOM/PRODUCTS/AVNG/L2A_CORFL/2021/06/04/SISTER_AVNG_L2A_CORFL_20210604T090303_001",
        fractional_cover_dataset="s3://s3.us-west-2.amazonaws.com:80/sister-ops-workspace/LOM/PRODUCTS/AVNG/L2B_FRCOV/2021/06/04/SISTER_AVNG_L2B_FRCOV_20210604T090303_001",
        crid="000",
        publish_to_cmr=False,
        cmr_metadata={},
        queue="sister-job_worker-16gb",
        identifier="WO_AP_20230425_AVNG_1")
    
    print(response.id, response.status)
