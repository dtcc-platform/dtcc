import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

# Download pointcloud and building footprints
pointcloud = dtcc.download_pointcloud(bounds=bounds)
buildings = dtcc.download_footprints(bounds=bounds)

# Remove global outliers
pointcloud = pointcloud.remove_global_outliers(3.0)

# Build terrain raster and mesh
raster = dtcc.builder.build_terrain_raster(pointcloud, cell_size=5, ground_only=True)
mesh = dtcc.builder.build_terrain_mesh(raster)

# Extract roof points and compute building heights
buildings = dtcc.extract_roof_points(buildings, pointcloud)
buildings = dtcc.compute_building_heights(buildings, raster, overwrite=True)

# Build LOD1 buildings
buildings = dtcc.builder.build_lod1_buildings(
    buildings, default_ground_height=raster.min, always_use_default_ground=True
)

# Create city and add buildings and geometries
city = dtcc.City()
city.add_buildings(buildings)
city.add_terrain(raster)
city.add_terrain(mesh)

# View city
city.view()
