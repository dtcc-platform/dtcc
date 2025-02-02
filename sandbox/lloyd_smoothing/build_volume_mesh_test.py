#!/usr/bin/env python
import sys
from pathlib import Path
from lloyd_smoothing_3d import lloyd_smoothing
from dtcc import *

# FIXME: Obscure imports
from dtcc_core.builder.model_conversion import (
    create_builder_polygon,
    create_builder_surface,
    builder_mesh_to_mesh,
    raster_to_builder_gridfield,
    builder_volume_mesh_to_volume_mesh,
)

# FIXME: Obscure imports
from dtcc_core.builder._dtcc_builder import build_ground_mesh, VolumeMeshBuilder

# FIXME: Debug plotting in Python
# from plotting import plot_mesh

# Domain bounds (for testing)
# bounds = Bounds(102000, 6213000, 103000, 6214000)
# bounds = Bounds(102000, 6213000, 102100, 6213100)
bounds = None

x0 = 99086.5
y0 = 6212830
x1 = 100294
y1 = 6214710
dx = x1 - x0
dy = y1 - y0
print(f"dx = {dx}, dy = {dy}")
# exit()
xm = (x0 + x1) / 2
ym = (y0 + y1) / 2
bounds = Bounds(x0 + 650, y0 + 1150, x1 - 100, y1 - 300)
print(bounds)
# bounds = Bounds(99548.0, 6212920.0, 99700.0, 6213050.0)
# bounds = Bounds(xmin=100050, ymin=6213370, xmax=100125, ymax=6213390)

# FIXME: Mix of parameters in dict and explicit function arguments below

# Set parameters
_parameters = {}
_parameters["max_mesh_size"] = 10
_parameters["min_mesh_angle"] = 30
_parameters["smoother_max_iterations"] = 5000
_parameters["smoothing_relative_tolerance"] = 0.0005
_parameters["debug_step"] = 3

# Set data paths
# data_directory = Path("../../data/helsingborg-residential-2022")
data_directory = Path("../../data/helsingborg-harbour-2022")
data_directory = Path("/Users/georgespaias/Scratch/development_dtcc/data/helsingborg-harbour-2022")
buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory / "PointCloud.las"

# FIXME: Can we get this data from dtcc-data?

# Load data
pointcloud = load_pointcloud(pointcloud_path, bounds=bounds)
footprints = load_footprints(buildings_path, bounds=bounds)

# FIXME: Are all operations on point clouds and footprints out-place?
# FIXME: Explicit parameter 3 for remove_global_outliers() is not clear.

# Remove global outliers
pointcloud = pointcloud.remove_global_outliers(3)

# FIXME: Simplify so user does not need to worry about doing 3 things:
# 1. Build terrain raster
# 2. Add roof points to footprints
# 3. Add building heights to footprints
# Also, does it make sense that footprints have roof heights?

# Build terrain raster
terrain = build_terrain_raster(pointcloud, cell_size=2, radius=3, ground_only=True)

# Save to file for debugging
with open("raster.csv", "w") as f:
    f.write(", ".join(str(x) for x in terrain.data.flatten()))
print(terrain.data.shape)

# import matplotlib.pyplot as plt
# import numpy as np
# Z = terrain.data
# ny, nx = terrain.shape
# x = np.linspace(terrain.bounds.xmin, terrain.bounds.xmax, nx)
# y = np.linspace(terrain.bounds.ymin, terrain.bounds.ymax, ny)
# X, Y = np.meshgrid(x, y)
# plt.figure()
# plt.imshow(Z, cmap="terrain", origin="lower")
# plt.figure()
# ax = plt.axes(projection="3d")
# ax.plot_surface(X, Y, Z, cmap="terrain")
# plt.show()
# exit()

# Extract roof points
footprints = extract_roof_points(
    footprints, pointcloud, statistical_outlier_remover=True
)

# Compute building heights
footprints = compute_building_heights(footprints, terrain, overwrite=True)

# FIXME: Rename merge_building_footprints() --> merge_footprints()
# FIXME: Rename simplify_building_footprints() --> simplify_footprints()
# FIXME: Rename fix_building_footprint_clearance() --> fix_footprint_clearance()
merge_footprints = merge_building_footprints
simplify_footprints = simplify_building_footprints
fix_footprint_clearance = fix_building_footprint_clearance

# FIXME: Can we simplify this as well? merge-simplify-fix in one function?
# FIXME: Quite a few parameters here. Can we simplify this?

# Merge and simplify building footprints
lod = GeometryType.LOD0
footprints = merge_footprints(footprints, lod=lod, max_distance=0.5, min_area=10)


footprints = simplify_footprints(footprints, 0.25, lod=lod)
footprints = fix_footprint_clearance(footprints, 0.5)

# FIXME: Is this the ideal resolution? Handle it automatically?


# Set subdomain resolution to half the building height
subdomain_resolution = [
    min(building.height, _parameters["max_mesh_size"]) for building in footprints
]

# subdomain_resolution = []


# FIXME: Should not need to convert from Python to C++.

# Convert from Python to C++
_footprints = [
    create_builder_polygon(building.lod0.to_polygon())
    for building in footprints
    if building is not None
]

# FIXME: Pass bounds as argument (not xmin, ymin, xmax, ymax).

# Build ground mesh
_ground_mesh = build_ground_mesh(
    _footprints,
    subdomain_resolution,
    terrain.bounds.xmin,
    terrain.bounds.ymin,
    terrain.bounds.xmax,
    terrain.bounds.ymax,
    _parameters["max_mesh_size"],
    _parameters["min_mesh_angle"],
    True,
)

# FIXME: Should not need to convert from C++ to Python mesh.

# Convert from C++ to Python
ground_mesh = builder_mesh_to_mesh(_ground_mesh)

# Save ground mesh to file
ground_mesh.save(data_directory / "ground_mesh.vtu")
ground_mesh.save("ground_mesh.pb")

# View ground mesh (for debugging)
# zoom = Bounds(102000, 6213000, 103000, 6214000)
# plot_mesh(ground_mesh, show_labels=True, bounds=zoom)
# ground_mesh.view()

# FIXME: Should not need to convert from Python to C++.
# FIXME: Why do we need to convert from raster to gridfield?

# Convert from Python to C++ and also from raster to gridfield
_dem = raster_to_builder_gridfield(terrain)

# FIXME: Should not need to convert from Python to C++.
# FIXME: Why do we need to convert from polygon to surface?

# Convert from Python to C++
_surfaces = [
    create_builder_surface(building.lod0)
    for building in footprints
    if building is not None
]

# FIXME: Should not need to create a VolumeMeshBuilder.
# FIXME: Should have a free function build_volume_mesh()

# Create volume mesh builder
volume_mesh_builder = VolumeMeshBuilder(_surfaces, _dem, _ground_mesh, 0.0)

# Build volume mesh
_volume_mesh = volume_mesh_builder.build(
    _parameters["smoother_max_iterations"],
    _parameters["smoothing_relative_tolerance"],
    0.0,
    _parameters["debug_step"],
)

# FIXME: Should not need to convert from C++ to Python

# Convert from C++ to Python
volume_mesh = builder_volume_mesh_to_volume_mesh(_volume_mesh)

# Save volume mesh to file
volume_mesh.save(data_directory / f"volume_mesh_original.vtu")

# LLoyd smoothing
volume_mesh = lloyd_smoothing(volume_mesh, iterations=10, alpha=0.2)
volume_mesh.save(data_directory / f"volume_mesh_lloyd.vtu")
