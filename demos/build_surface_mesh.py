#!/usr/bin/env python
import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

# Download pointcloud and footprints
pointcloud = dtcc.download_pointcloud(bounds=bounds)
footprints = dtcc.download_footprints(bounds=bounds)

# Remove global outliers
pointcloud = pointcloud.remove_global_outliers(3.0)

# Build terrain raster
terrain_raster = dtcc.build_terrain_raster(
    pointcloud, cell_size=2, radius=3, ground_only=True
)

# Extract roof points and comput building heights
footprints = dtcc.extract_roof_points(
    footprints, pointcloud, statistical_outlier_remover=True
)
footprints = dtcc.compute_building_heights(
    footprints, terrain_raster, overwrite=True
)

# Create city and add geometries
city = dtcc.City()
city.add_terrain(terrain_raster)
city.add_buildings(footprints, True)

# FIXME: Rename --> build_mesh

# Build surface mesh
mesh = dtcc.build_surface_mesh(
    city,
    lod=dtcc.GeometryType.LOD0,
    min_building_detail=0.5,
    min_building_area=10,
    building_mesh_triangle_size=2,
    max_mesh_size=10,
    min_mesh_angle=25,
    smoothing=3,
)

# View mesh
mesh.view()
