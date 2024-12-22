#!/usr/bin/env python

import dtcc

from pathlib import Path

data_directory = Path(__file__).parent / ".." / "data" / "helsingborg-residential-2022"
buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory / "pointcloud.las"

footprints = dtcc.io.load_footprints(buildings_path, "uuid")

pc = dtcc.io.load_pointcloud(pointcloud_path)
pc = pc.remove_global_outliers(3)

terrain_raster = dtcc.builder.build_terrain_raster(
    pc, cell_size=2, radius=3, ground_only=True
)

footprints = dtcc.builder.extract_roof_points(
    footprints, pc, statistical_outlier_remover=True
)

footprints = dtcc.builder.compute_building_heights(
    footprints, terrain_raster, overwrite=True
)

print("Creating city")
city = dtcc.City()

terrain_raster = dtcc.builder.build_terrain_raster(
    pc, cell_size=2, radius=3, ground_only=True
)
city.add_terrain(terrain_raster)

city.add_buildings(footprints, True)

surface_mesh = dtcc.builder.build_surface_mesh(
    city,
    lod=dtcc.GeometryType.LOD0,
    min_building_detail=0.5,
    min_building_area=10,
    building_mesh_triangle_size=2,
    max_mesh_size=10,
    min_mesh_angle=25,
    smoothing=3,
)
surface_mesh.view()
