from setuptools import setup, find_packages
import os, sys
import glob
from subprocess import PIPE, Popen
Version = "8.2.1"
p = Popen(
    ("git",
     "describe",
     "--tags"),
    stdin=PIPE,
    stdout=PIPE,
    stderr=PIPE)
try:
    descr = p.stdout.readlines()[0].strip().decode("utf-8")
    Version = "-".join(descr.split("-")[:-2])
    if Version == "":
        Version = descr
except:
    descr = Version

 
buttons = glob.glob("data/buttons/*")
coast_low = glob.glob("data/coastline/low/*")
coast_medium = glob.glob("data/coastline/medium/*")
coast_high = glob.glob("data/coastline/high/*")
package_data = ['data/earth2k.jpg', 'data/colormaps.pkl', 'data/parameters.txt']
packages = find_packages()

setup (name="DV3D",
       version=descr,
       description="Climate Data Interactive Visualization System",
       url="http://portal.nccs.nasa.gov/DV3D/",
       packages=packages,
       data_files=[('share/dv3d', package_data),
                   ('share/dv3d/buttons', buttons),
                   ('share/dv3d/coastline', ('data/coastline/index.txt',)),
                   ('share/dv3d/coastline/low', coast_low),
                   ('share/dv3d/coastline/medium', coast_medium),
                   ('share/dv3d/coastline/high', coast_high),
                   ]
       )
