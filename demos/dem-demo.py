from pathlib import Path
import dtcc


folder = Path("data") #Data folder
file_list = [f for f in folder.iterdir() if f.suffix == ".tif"] #Load all .tif files from data folder

raster =  dtcc.io.raster.load(file_list)
pointcloud = raster.to_pointcloud()
# Build terrain raster
raster = dtcc.build_terrain_raster(pointcloud, cell_size=10)

# View terrain raster
raster.view()