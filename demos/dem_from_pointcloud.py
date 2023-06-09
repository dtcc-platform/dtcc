import dtcc
from pathlib import Path

data_dir = Path(__file__).parent / ".." / "data" / "HelsingborgResidential2022"

### Create a new DEM from a point cloud

# load a point cloud
pc = dtcc.io.load_pointcloud(data_dir / "PointCloud.las")

# remove global outliers more than 3 standard deviations from the mean
# then rasterize the point cloud to a DEM with a cell size of 0.5 m,
# using a radius of 3 m to interpolate the points. Use only points
# classified as ground or water.
dem = pc.remove_global_outliers(3).rasterize(cell_size=0.5, radius=3, ground_only=True)
dem.save(data_dir / "dem.tif")
