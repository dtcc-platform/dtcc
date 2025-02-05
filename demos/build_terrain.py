# This demo illustrates how to build a terrain from a point cloud.

import dtcc

# Define the bounding box for the Helsingborg residential area. 
# These coordinates specify the area of interest to be passed into the 
bounds = dtcc.Bounds(
    xmin=319891.0,
    ymin=6399790.0,
    xmax=319891.0+2000.0,
    ymax=6399790.0+2000.0
)

# Download point cloud
pointcloud = dtcc.data.download_data(data_type='lidar', provider= 'dtcc', user_bbox=bounds)

# Remove global outliers
pointcloud = pointcloud.remove_global_outliers(3.0)

# Build terrain
terrain = dtcc.builder.build_terrain_mesh(
    pointcloud,
    max_mesh_size=10,
    min_mesh_angle=25,
    smoothing=3,
)

# View mesh
terrain.mesh.view()
