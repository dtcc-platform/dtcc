# Copyright (C) 2023 Dag Wästberg
# Licensed under the MIT License
#
# This demo illustrates how to generate a terrain mesh from a point cloud.

import dtcc
from pathlib import Path

# Set data paths
data_directory = (
    Path(__file__).parent.resolve() / "../data/helsingborg-residential-2022"
)
buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory / "pointcloud.las"


pointcloud = dtcc.io.load_pointcloud(pointcloud_path)
pointcloud = pointcloud.remove_global_outliers(3.0)

# print(f"City has {len(city.buildings)} buildings with bounding boxes {city.bounds}")

terrain = dtcc.builder.build_terrain_mesh(
    pointcloud=pointcloud,
    max_mesh_size=10,
    min_mesh_angle=25,
    smoothing=3,
)
print(f"Terrain mesh: {terrain}")
# print(f"Ground mesh: {ground_mesh}")
terrain.mesh.view()
