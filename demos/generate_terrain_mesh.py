# Copyright (C) 2023 Dag Wästberg
# Licensed under the MIT License
#
# This demo illustrates how to generate a terrain mesh from a point cloud.

from dtcc import builder, load_city, load_pointcloud

from pathlib import Path

# Set data paths
data_directory = Path("../data/helsingborg-residential-2022")
buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory / "pointcloud.las"

city = load_city(buildings_path)
pointcloud = load_pointcloud(pointcloud_path)

city = city.terrain_from_pointcloud(
    pointcloud,
    cell_size=1.0,
    window_size=5,
    ground_only=True,
)


builder_city = builder.model.create_builder_city(city)
builder_dem = builder.model.raster_to_builder_gridfield(city.terrain)

ground_mesh = builder._dtcc_builder.build_mesh(builder_city, builder_dem, 2.0, True)
ground_mesh = ground_mesh[0]

ground_mesh = builder.model.builder_mesh_to_mesh(ground_mesh)

ground_mesh.view(pc=pointcloud)
