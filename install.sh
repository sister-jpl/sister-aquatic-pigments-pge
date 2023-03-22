pge_dir=$(cd "$(dirname "$0")" ; pwd -P)
app_dir=$(dirname ${pge_dir})

pushd $app_dir
git clone https://github.com/EnSpec/sister-mdn_chlorophyll.git -b master
git clone https://github.com/EnSpec/sister-mdn_phycocyanin.git -b main

# Copy model weights file to chlorophyll

aws cp http://s3//sister-ops-registry/packages/mdn_chlorophyll_weights/HICO/45313342cb628c8cf45b6e2e29f4dc9a780ee1d403bdb98461e28fcb13ad9ce3.zip sister-mdn_chlorophyll/MDN/Weights/HICO/45313342cb628c8cf45b6e2e29f4dc9a780ee1d403bdb98461e28fcb13ad9ce3.zip

# Create conda environment for chlorophyll-a
conda create -n ap-chla -y python=3.8 gdal
source activate ap-chla

pushd sister-mdn_chlorophyll
pip install -e .

conda deactivate
popd

# Create conda environment for phycocyanin
conda create -n ap-phyco -y python=3.7 gdal
source activate ap-phyco

pushd sister-mdn_phycocyanin
pip install -e .
