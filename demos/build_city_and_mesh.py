# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License
#
# This demo illustrates how to build a city model from raw data,
# essentially equivalent to running the dtcc-build command-line
# utility, but with more control over the process.

from dtcc import *
from pathlib import Path

# Set data paths
data_directory = Path("HelsingborgResidential2022")
buildings_path = data_directory / "PropertyMap.shp"
pointcloud_path = data_directory

# Set parameters
p = parameters.default()
p["auto_domain"] = True

# Calculate bounds
origin, bounds = calculate_bounds(buildings_path, pointcloud_path, p)

# Load data from file
city = load_city(data_directory / "PropertyMap.shp", bounds=bounds)
point_cloud = load_pointcloud(data_directory, bounds=bounds)

# Build city
city = build_city(city, point_cloud, bounds, p)

# Save data to file
city.save(data_directory / "city.pb")

# View data
city.view()
point_cloud.view()
