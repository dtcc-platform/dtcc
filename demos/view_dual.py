# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License
#
# This demo illustrates how to build a city model from raw data,
# and viewing the resulting mesh model together with the pointcloud.

from pathlib import Path
from dtcc import *

# Build a mesh from raw data
data_directory = Path("../data/dtcc-demo-data/helsingborg-residential-2022")
p = parameters.default()
p["data_directory"] = data_directory
build(p)

buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory

origin, bounds = calculate_bounds(buildings_path, pointcloud_path, p)
city = load_city(buildings_path, bounds=bounds)
pointcloud = load_pointcloud(pointcloud_path, bounds=bounds)

# Build a city
city = build_city(city, pointcloud, bounds, p)

# From the city build meshes
volume_mesh, boundary_mesh = build_volume_mesh(city)

boundary_mesh.view(pc=pointcloud)
