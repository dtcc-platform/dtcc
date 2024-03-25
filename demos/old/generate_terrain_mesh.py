# Copyright (C) 2023 Dag Wästberg
# Licensed under the MIT License
#
# This demo illustrates how to generate a terrain mesh from a point cloud.

from dtcc import builder, load_city, load_pointcloud

from pathlib import Path

# Set data paths
data_directory = (
    Path(__file__).parent.resolve() / "../data/helsingborg-residential-2022"
)
buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory / "pointcloud.las"

city = load_city(buildings_path)
pointcloud = load_pointcloud(pointcloud_path)

pointcloud = pointcloud.remove_global_outliers(3.0)

city = city.terrain_from_pointcloud(
    pointcloud,
    cell_size=1.0,
    window_size=5,
    ground_only=True,
)

# print(f"City has {len(city.buildings)} buildings with bounding boxes {city.bounds}")

ground_mesh = builder.meshing.terrain_mesh(
    city, max_mesh_size=5.0, min_mesh_angle=25, smoothing=3, include_footprints=False
)
print(f"Ground mesh: {ground_mesh}")
ground_mesh.view(pc=pointcloud)
