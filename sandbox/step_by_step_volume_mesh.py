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
    builder_volume_mesh_to_volume_mesh,
)

from dtcc_builder import _dtcc_builder

from pathlib import Path

from time import time

import sys

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
builder_footprints = [
    create_builder_polygon(building.lod0.to_polygon())
    for building in clearance_fix
    if building is not None
]
max_mesh_size = 10
min_mesh_angle = 25
smoothing = 3
merge_meshes = True
domain_height = 30
layer_height = 3

smoother_max_iterations = 1000
smoothing_relative_tolerance = 0.001

# Step 3.1: Build ground mesh

builder_ground_mesh = _dtcc_builder.build_ground_mesh(
    builder_footprints,
    subdomain_resolution,
    terrain_raster.bounds.xmin,
    terrain_raster.bounds.ymin,
    terrain_raster.bounds.xmax,
    terrain_raster.bounds.ymax,
    max_mesh_size,
    min_mesh_angle,
    True,  # sort triangles
)

ground_mesh = builder_mesh_to_mesh(builder_ground_mesh)
print(
    f"Ground mesh has: {len(ground_mesh.vertices)} vertices and {len(ground_mesh.faces)} faces"
)
# ground_mesh.view()

# Step 3.2: Layer ground mesh

start_time = time()

layer_heights = [2, 2, 4, 7, 10, 20]
# layer_heights = [10, 10, 10, 10]

volume_mesh = _dtcc_builder.layer_ground_mesh(builder_ground_mesh, layer_heights)

print(f"Layering took {time() - start_time} seconds")

layer_mesh = builder_volume_mesh_to_volume_mesh(volume_mesh)
print(
    f"layer mesh has: {len(layer_mesh.vertices)} vertices and {len(layer_mesh.cells)} cells"
)

# layer_mesh.save("layer_mesh.vtu")
# layer_mesh_surface = _dtcc_builder.compute_boundary_mesh(volume_mesh)
# layer_mesh_surface = builder_mesh_to_mesh(layer_mesh_surface)
# layer_mesh_surface.view()
# sys.exit(0)
# layer_mesh.view()

# Step 3.3: mooth volume mesh (set ground height)

domain_height = sum(layer_heights)
top_height = domain_height + terrain_raster.data.max()

volume_mesh = _dtcc_builder.smooth_volume_mesh(
    volume_mesh,
    [],
    builder_dem,
    top_height,
    False,
    smoother_max_iterations,
    smoothing_relative_tolerance,
)


smoothed_mesh = builder_volume_mesh_to_volume_mesh(volume_mesh)
print(
    f"smoothed mesh has: {len(smoothed_mesh.vertices)} vertices and {len(smoothed_mesh.cells)} cells"
)
smoothed_mesh.save("smoothed_mesh.vtu")


# Step 3.4: Trim volume mesh (remove building interiors)
volume_mesh = _dtcc_builder.trim_volume_mesh(
    volume_mesh, builder_ground_mesh, builder_surfaces
)

trimmed_mesh = builder_volume_mesh_to_volume_mesh(volume_mesh)
print(
    f"trimmed mesh has: {len(trimmed_mesh.vertices)} vertices and {len(trimmed_mesh.cells)} cells"
)

trimmed_mesh.save("trimmed_mesh.vtu")

# Step 3.5: Smooth volume mesh (set ground and building heights)
volume_mesh = _dtcc_builder.smooth_volume_mesh(
    volume_mesh,
    builder_surfaces,
    builder_dem,
    top_height,
    True,
    smoother_max_iterations,
    smoothing_relative_tolerance,
)

volume_mesh = builder_volume_mesh_to_volume_mesh(volume_mesh)

print(
    f"z min: {volume_mesh.vertices[:, 2].min()} z max: {volume_mesh.vertices[:, 2].max()}"
)

volume_mesh.save("volume_mesh_new3.vtu")
# volume_mesh.view()
