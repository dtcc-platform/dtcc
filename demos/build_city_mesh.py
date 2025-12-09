# This demo illustrates how to build a city mesh from a point cloud and footprints.

import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

# Download pointcloud and building footprints
pointcloud = dtcc.download_pointcloud(bounds=bounds)
buildings = dtcc.download_footprints(bounds=bounds)

# Remove global outliers
pointcloud = pointcloud.remove_global_outliers(3.0)

# Build terrain raster
raster = dtcc.build_terrain_raster(pointcloud, cell_size=2, radius=3, ground_only=True)

# Extract roof points and compute building heights
buildings = dtcc.extract_roof_points(buildings, pointcloud)
buildings = dtcc.compute_building_heights(buildings, raster, overwrite=True)

# Create city and add geometries
city = dtcc.City()
city.add_terrain(raster)
city.add_buildings(buildings, remove_outside_terrain=True)

# Build city mesh
mesh = dtcc.build_city_mesh(city, lod=dtcc.GeometryType.LOD1)

# View mesh
mesh.view()
