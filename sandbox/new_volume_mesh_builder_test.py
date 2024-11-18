#!/usr/bin/env python

from dtcc import *

from dtcc_core.builder.model_conversion import (
    create_builder_polygon,
    create_builder_surface,
    builder_mesh_to_mesh,
    raster_to_builder_gridfield,
    builder_volume_mesh_to_volume_mesh,
)

from dtcc_core.builder import _dtcc_builder
from pathlib import Path
from time import time
import sys

# Parameters
_parameters = {}
_parameters["max_mesh_size"] = 10
_parameters["min_mesh_angle"] = 25
_parameters["smoothing"] = 3
_parameters["merge_meshes"] = True
_parameters["domain_height"] = 30
_parameters["layer_height"] = 3
_parameters["smoother_max_iterations"] = 1000
_parameters["smoothing_relative_tolerance"] = 0.001
_parameters["domain_padding_height"] = 0.0
_parameters["debug_step"] = 5

data_directory = Path(__file__).parent / ".." / "data" / "helsingborg-residential-2022"
buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory / "PointCloud.las"


footprints = load_footprints(buildings_path, "uuid")

pc = load_pointcloud(pointcloud_path)
pc = pc.remove_global_outliers(3)

terrain_raster = build_terrain_raster(
    pc, cell_size=2, radius=3, ground_only=True
)

# caluclate the building heights
footprints = extract_roof_points(
    footprints, pc, statistical_outlier_remover=True
)

footprints = compute_building_heights(
    footprints, terrain_raster, overwrite=True
)

# merge and simplify the building footprints
merged_footprints = merge_building_footprints(
    footprints, lod=GeometryType.LOD0, max_distance=0.5, min_area=10
)
simplifed_footprints = simplify_building_footprints(
    merged_footprints, 0.25, lod=GeometryType.LOD0
)
clearance_fix = fix_building_footprint_clearance(simplifed_footprints, 0.5)

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


# Build ground mesh
builder_ground_mesh = _dtcc_builder.build_ground_mesh(
    builder_footprints,
    subdomain_resolution,
    terrain_raster.bounds.xmin,
    terrain_raster.bounds.ymin,
    terrain_raster.bounds.xmax,
    terrain_raster.bounds.ymax,
    _parameters["max_mesh_size"],
    _parameters["min_mesh_angle"],
    True,  # sort triangles
)

ground_mesh = builder_mesh_to_mesh(builder_ground_mesh)
info(ground_mesh)

# Save ground mesh to file
ground_mesh.save(data_directory / "ground_mesh.vtu")

# FIXME: Why is an object needed, why not use static functions?
volume_mesh_builder = _dtcc_builder.VolumeMeshBuilder(  builder_surfaces,
                                                        builder_dem,
                                                        builder_ground_mesh,
                                                        _parameters["domain_height"])

# Build volume mesh
builder_volume_mesh = volume_mesh_builder.build(_parameters["smoother_max_iterations"],
                                                _parameters["smoothing_relative_tolerance"],
                                                _parameters["domain_padding_height"],
                                                _parameters["debug_step"])

# Convert to Python mesh
volume_mesh = builder_volume_mesh_to_volume_mesh(builder_volume_mesh)
info(volume_mesh)

# Save volume mesh to file
volume_mesh.save(data_directory / "volume_mesh.vtu")


# FIXME
#
# 1. Print mesh quality at each stage
