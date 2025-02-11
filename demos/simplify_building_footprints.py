import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

footprints = dtcc.download_data(
    data_type="footprints", provider="dtcc", user_bbox=bounds
)

pc = dtcc.download_data(data_type="lidar", provider="dtcc", user_bbox=bounds)
pc = pc.remove_global_outliers(3)

terrain_raster = dtcc.build_terrain_raster(pc, cell_size=2, radius=3, ground_only=True)

footprints = dtcc.extract_roof_points(footprints, pc, statistical_outlier_remover=True)
footprints = dtcc.compute_building_heights(footprints, terrain_raster, overwrite=True)

merged_footprints = dtcc.merge_building_footprints(
    footprints, lod=dtcc.GeometryType.LOD0, max_distance=0.5, min_area=10
)
simplifed_footprints = dtcc.simplify_building_footprints(
    merged_footprints, 0.25, lod=dtcc.GeometryType.LOD0
)
clearance_fix = dtcc.fix_building_footprint_clearance(simplifed_footprints, 0.5)


max_wall_length = [building.height for building in clearance_fix]


split_walls = dtcc.split_footprint_walls(clearance_fix, max_wall_length=max_wall_length)

city = dtcc.City()
city.add_buildings(split_walls)

city.view()
