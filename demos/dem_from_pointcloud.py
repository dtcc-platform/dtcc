# This demo shows how to create a DEM from a point cloud.

from dtcc import io

# Load point cloud
pc = io.load_pointcloud("./dtcc-demo-data/HelsingborgResidential2022/PointCloud.las")

# Remove global outliers more than 3 standard deviations from the mean,
# then rasterize the point cloud to a DEM with a cell size of 0.5m
# and a radius of 3m to interpolate the points, using only points
# classified as ground or water.
dem = pc.remove_global_outliers(3).rasterize(cell_size=0.5, radius=3, ground_only=True)

# Save DEM to file
dem.save("dem.tif")
