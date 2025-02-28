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

# Simplify building footprints
buildings = dtcc.merge_building_footprints(buildings, max_distance=0.5, min_area=10)
buildings = dtcc.simplify_building_footprints(buildings, tolerance=0.25)
buildings = dtcc.fix_building_footprint_clearance(buildings, 0.5)

# Split building footprints walls
max_wall_length = [building.height for building in buildings]
buildings = dtcc.split_footprint_walls(buildings, max_wall_length=max_wall_length)

# Create city and add buildings
city = dtcc.City()
city.add_buildings(buildings)

# View city
city.view()
