#!/usr/bin/env python3
import dtcc

# import dtcc_viewer


# Define the bounding box for the Helsingborg residential area. 
# These coordinates specify the area of interest to be passed into the 
bounds = dtcc.Bounds(
    xmin=319891,
    ymin=6399790,
    xmax=319891+2000,
    ymax=6399790+2000
)

footprints = dtcc.download_data(data_type='footprints', provider= 'dtcc', user_bbox=bounds)

pointcloud = dtcc.download_data(data_type='lidar', provider= 'dtcc', user_bbox=bounds)
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
