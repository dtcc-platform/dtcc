#!/usr/bin/env python3
import dtcc
import dtcc_viewer

# import dtcc_viewer
from pathlib import Path

data_directory = Path(__file__).parent / ".." / "data" / "helsinborg-residential-2022"
buildings_path = data_directory / "PropertyMap.shp"
pointcloud_path = data_directory / "PointCloud.las"

footprints = dtcc.io.load_footprints(buildings_path, "uuid")

pc = dtcc.io.load_pointcloud(pointcloud_path)
pc = pc.remove_global_outliers(3)

terrain_raster = dtcc.builder.build_terrain_raster(
    pc, cell_size=2, radius=3, ground_only=True
)
terrain_mesh = dtcc.builder.build_terrain_mesh(terrain_raster)

footprints = dtcc.builder.extract_roof_points(
    footprints, pc, statistical_outlier_remover=True
)
footprints = dtcc.builder.compute_building_heights(
    footprints, terrain_raster, overwrite=True
)

lod1_buildings = dtcc.builder.build_lod1_buildings(
    footprints, default_ground_height=terrain_raster.min, always_use_default_ground=True
)
city = dtcc.City()
city.add_terrain(terrain_raster)
city.add_terrain(terrain_mesh)
city.add_buildings(lod1_buildings)

print(f"loaded {len(city.buildings)} buildings")


city.view()
