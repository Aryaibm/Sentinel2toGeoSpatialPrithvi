 #!/bin/bash

 curl https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -o ~/miniconda.sh
 wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh 
 bash ~/miniconda.sh -b -p $HOME/miniconda
 eval "$(/$HOME/miniconda/bin/conda shell.bash hook)"
 conda install -c conda-forge gdal
 conda install pillow
 conda install -c conda-forge rasterio
 conda install matplotlib
 conda install conda-forge::glob2
 export PYTHONWARNINGS="ignore"