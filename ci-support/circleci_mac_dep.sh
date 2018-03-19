#!/usr/bin/env bash
ls
pwd
export PATH=${HOME}/miniconda/bin:${PATH}
conda create -q -n py2 -c cdat/label/nightly -c nesii/label/dev-esmf -c conda-forge -c uvcdat cdms2 cdat_info udunits2 nose flake8 image-compare matplotlib numpy=1.13 genutil vtk-cdat cdutil vcs "proj4<5" "python<3"
conda install -q -n py2 -c cdat/label/nightly -c conda-forge mesalib
conda create -q -n py3 -c cdat/label/nightly -c nesii/label/dev-esmf -c conda-forge -c uvcdat cdms2 cdat_info udunits2 nose flake8 image-compare matplotlib numpy=1.13 genutil vtk-cdat cdutil vcs "proj4<5" "python>3"
conda install -q -n py3 -c cdat/label/nightly -c conda-forge mesalib
export UVCDAT_ANONYMOUS_LOG=False
source activate py2
python setup.py install
source activate py3
python setup.py install
