#!/usr/bin/env python3
import dtcc
import dtcc_viewer
from pathlib import Path

data_directory = Path(__file__).parent / ".." / "data" / "HelsingborgResidential2022"
buildings_path = data_directory / "PropertyMap.shp"
pointcloud_path = data_directory / "PointCloud.las"

import dtcc

footprints = dtcc.io.load_footprints(buildings_path, "uuid")

pc = dtcc.io.load_pointcloud(pointcloud_path)
pc = pc.remove_global_outliers(3)

terrain = dtcc.builder.build_terrain_raster(pc, cell_size=2, radius=3, ground_only=True)

footprints = dtcc.builder.extract_roof_points(footprints, pc)
footprints = dtcc.builder.compute_building_heights(footprints, terrain)

lod1_buildings = dtcc.builder.build_lod1_buildings(footprints)
print(lod1_buildings[157].lod0.vertices)
city = dtcc.City()
city.add_terrain(terrain)
city.add_buildings(lod1_buildings)

print(city.buildings[157].geometry[dtcc.GeometryType.LOD1])
# city.view()
