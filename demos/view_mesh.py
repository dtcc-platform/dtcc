# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License
#
# This demo illustrates how to build a city model from raw data,
# and viewing the resulting mesh model together with the pointcloud.

from pathlib import Path
import numpy as np
import dtcc


# Build a mesh from raw data
data_directory = Path(__file__).parent / ".." / "data/helsingborg-residential-2022"
p = dtcc.builder.parameters.default()
p["data_directory"] = data_directory

buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory

origin, bounds = dtcc.builder.calculate_bounds(buildings_path, pointcloud_path, p)
city = dtcc.io.load_city(buildings_path, bounds=bounds)
pointcloud = dtcc.io.load_pointcloud(pointcloud_path, bounds=bounds)

# Build a city
city = dtcc.builder.build_city(city, pointcloud, bounds, p)

# From the city build meshes
ground_mesh = dtcc.builder.build_terrain_mesh(city, p)
building_meshes = dtcc.builder.build_building_meshes(city, p)
building_mesh = dtcc.builder.meshing.merge_meshes(building_meshes)

# Toggle the viewin_option variable between 1,2,3 to try different modes of viewing.
viewing_option = 3

# View the building mesh with default colors
if viewing_option == 1:
    building_mesh.view()

# View the building mesh with data per vertex
elif viewing_option == 2:
    data = building_mesh.vertices[:, 1]

    # View the building mesh and append colors
    building_mesh.view(data=data)

# View the building mesh with an appended array of colors matching the vertex count
elif viewing_option == 3:
    # Normalise the data so it falls in the range [0,1]
    min = building_mesh.vertices[:, 1].min()
    max = building_mesh.vertices[:, 1].max()
    color_data = (building_mesh.vertices[:, 1] - min) / (max - min)

    # Create an np array with colors matching the number of vertices of the mesh.
    colors = np.zeros((len(building_mesh.vertices), 3))
    colors[:, 1] = color_data

    # View the building mesh and appedn colors
    building_mesh.view(colors=colors)
