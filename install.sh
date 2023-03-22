pge_dir=$(cd "$(dirname "$0")" ; pwd -P)
app_dir=$(dirname ${pge_dir})

cd $app_dir
git clone https://github.com/EnSpec/sister-mdn_chlorophyll.git -b master
git clone https://github.com/EnSpec/sister-mdn_phycocyanin.git -b main

# Create conda environment
conda create -n aquatic-pigments -y -c conda-forge python=3.8 gdal
source activate aquatic-pigments

cd sister-mdn_chlorophyll
pip install -e .

cd ../sister-mdn_phycocyanin
pip install -e .
