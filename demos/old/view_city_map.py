import dtcc
from pathlib import Path

# Set data paths
data_directory = Path(__file__).parent / ".." / "data/helsingborg-harbour-2022"
buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory

# Set parameters
p = dtcc.parameters.default()
p["auto_domain"] = True
# Calculate bounds
origin, bounds = dtcc.calculate_bounds(buildings_path, pointcloud_path, p)

# Load data from file
city = dtcc.io.load_city(buildings_path, bounds=bounds)
pointcloud = dtcc.io.load_pointcloud(pointcloud_path, bounds=bounds)

# Build city model
city = dtcc.build_city(city, pointcloud, bounds, p)

city.view()
