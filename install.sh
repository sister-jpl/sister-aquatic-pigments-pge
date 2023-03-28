pge_dir=$(cd "$(dirname "$0")" ; pwd -P)
app_dir=$(dirname ${pge_dir})

# Clone the repositories into the app directory

pushd $app_dir
git clone https://github.com/EnSpec/sister-mdn_chlorophyll.git -b master
git clone https://github.com/EnSpec/sister-mdn_phycocyanin.git -b main

# Create conda environment for chlorophyll-a and install
conda create -n ap-chla -y -c conda-forge python=3.8 gdal=3.1 awscli=1
source activate ap-chla

pushd sister-mdn_chlorophyll
aws s3 cp s3://sister-ops-registry/packages/mdn_chlorophyll_weights/HICO/45313342cb628c8cf45b6e2e29f4dc9a780ee1d403bdb98461e28fcb13ad9ce3.zip MDN/Weights/HICO/45313342cb628c8cf45b6e2e29f4dc9a780ee1d403bdb98461e28fcb13ad9ce3.zip
pip install -e .

conda deactivate
popd

# Create conda environment for phycocyanin and install
conda create -n ap-phyco -y python=3.7.16 gdal=3
source activate ap-phyco

pushd sister-mdn_phycocyanin
pip install -e .
