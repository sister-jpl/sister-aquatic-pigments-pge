pge_dir=$(cd "$(dirname "$0")" ; pwd -P)
app_dir=$(dirname ${pge_dir})

pushd $app_dir
git clone https://github.com/EnSpec/sister-mdn_chlorophyll.git -b master
git clone https://github.com/EnSpec/sister-mdn_phycocyanin.git -b main

# Create conda environment for chlorophyll-a
conda create -n ap-chla -y python=3.8 gdal
source activate ap-chla

pushd sister-mdn_chlorophyll
pip install -e .

conda deactivate
popd

# Create conda environment for phycocyanin
conda create -n ap-phyco -y python=3.7.16 gdal
source activate ap-phyco

pushd sister-mdn_phycocyanin
pip install -e .
