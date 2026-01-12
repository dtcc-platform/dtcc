"""
Build a terrain raster from DEM GeoTIFF files.

This demo loads one or more DEM (.tif) files, converts them to a point cloud,
and builds a terrain raster at a specified resolution.
"""
from pathlib import Path
import dtcc


input_dir = Path("data") #Data folder
tif_list = [f for f in input_dir.iterdir() if f.suffix == ".tif"] #Load all .tif files from data folder

raster = dtcc.load_raster(tif_list)
pointcloud = raster.to_pointcloud()

# Build terrain raster
raster = dtcc.build_terrain_raster(pointcloud, cell_size=10)

# View terrain raster
raster.view()