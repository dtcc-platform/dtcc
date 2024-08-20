#!/usr/bin/env python

import dtcc


from dtcc_builder.model import (
    create_builder_polygon,
    create_builder_surface,
    create_builder_multisurface,
    builder_mesh_to_mesh,
    mesh_to_builder_mesh,
    create_builder_city,
    raster_to_builder_gridfield,
)

from dtcc_builder import _dtcc_builder

from pathlib import Path

data_directory = Path(__file__).parent / ".." / "data" / "HelsingborgResidential2022"
buildings_path = data_directory / "PropertyMap.shp"
pointcloud_path = data_directory / "PointCloud.las"

footprints = dtcc.io.load_footprints(buildings_path, "uuid")

pc = dtcc.io.load_pointcloud(pointcloud_path)
pc = pc.remove_global_outliers(3)

terrain_raster = dtcc.builder.build_terrain_raster(
    pc, cell_size=2, radius=3, ground_only=True
)

# caluclate the building heights
footprints = dtcc.builder.extract_roof_points(
    footprints, pc, statistical_outlier_remover=True
)

footprints = dtcc.builder.compute_building_heights(
    footprints, terrain_raster, overwrite=True
)

# merge and simplify the building footprints
merged_footprints = dtcc.builder.merge_building_footprints(
    footprints, lod=dtcc.model.GeometryType.LOD0, max_distance=0.5, min_area=10
)
simplifed_footprints = dtcc.builder.simplify_building_footprints(
    merged_footprints, 0.25, lod=dtcc.model.GeometryType.LOD0
)
clearance_fix = dtcc.builder.fix_building_footprint_clearance(simplifed_footprints, 0.5)

# set subdomain resolution to half the building height
subdomain_resolution = [building.height / 2 for building in clearance_fix]

# convert to C++ classes
builder_dem = raster_to_builder_gridfield(terrain_raster)
builder_surfaces = [
    create_builder_surface(building.lod0)
    for building in clearance_fix
    if building is not None
]

max_mesh_size = 10
min_mesh_angle = 25
smoothing = 3
merge_meshes = True

builder_surface_mesh = _dtcc_builder.build_city_surface_mesh(
    builder_surfaces,
    subdomain_resolution,
    builder_dem,
    max_mesh_size,
    min_mesh_angle,
    smoothing,
    merge_meshes,
)

result_mesh = builder_mesh_to_mesh(builder_surface_mesh[0])

result_mesh.view()
