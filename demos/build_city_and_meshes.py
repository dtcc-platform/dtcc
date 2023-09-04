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
pointcloud = load_pointcloud(data_directory, bounds=bounds)

# Build city model
city = build_city(city, pointcloud, bounds, p)

# Build ground mesh and building mesh (surface meshes)
ground_mesh, building_mesh = build_mesh(city, p)

# Build city mesh and volume mesh (tetrahedral mesh)
mesh, volume_mesh = build_volume_mesh(city, p)

# Save data to file
city.save(data_directory / "city.pb")
ground_mesh.save(data_directory / "ground_mesh.pb")
building_mesh.save(data_directory / "building_mesh.pb")
mesh.save(data_directory / "mesh.pb")
volume_mesh.save(data_directory / "volume_mesh.pb")

# View data
city.view()
pointcloud.view()
