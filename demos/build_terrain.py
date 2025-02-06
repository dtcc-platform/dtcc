# This demo illustrates how to build a terrain from a point cloud.

import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

# Download point cloud
pointcloud = dtcc.download_pointcloud(bounds=bounds)

# Remove global outliers
pointcloud = pointcloud.remove_global_outliers(3.0)

# Build terrain
terrain = dtcc.build_terrain(
    pointcloud,
    max_mesh_size=10,
    min_mesh_angle=25,
    smoothing=3,
)

# View terrain
terrain.view()
