from setuptools import setup, find_packages
import os, sys

package_data = ['data/earth2k.jpg', 'data/colormaps.pkl', 'data/parameters.txt', 'data/buttons/*', 'data/coastline/index.txt', 'data/coastline/low/*', 'data/coastline/medium/*', 'data/coastline/high/*']
packages = find_packages()

print("PKGS:",packages)
setup (name = "DV3D",
       description = "Climate Data Interactive Visualization System",
       url = "http://portal.nccs.nasa.gov/DV3D/",
       packages = packages,
       data_files=[('share/dv3d', package_data)]
       )

