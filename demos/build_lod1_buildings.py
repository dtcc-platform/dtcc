import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

footprints = dtcc.download_data(
    data_type="footprints", provider="dtcc", user_bbox=bounds
)

pointcloud = dtcc.download_data(data_type="lidar", provider="dtcc", user_bbox=bounds)
pointcloud = pointcloud.remove_global_outliers(3.0)

terrain_raster = dtcc.builder.build_terrain_raster(
    pointcloud, cell_size=2, radius=3, ground_only=True
)
terrain_mesh = dtcc.builder.build_terrain_mesh(terrain_raster)

footprints = dtcc.builder.extract_roof_points(
    footprints, pointcloud, statistical_outlier_remover=True
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
