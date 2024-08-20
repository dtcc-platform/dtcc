# This demo illustrates how to build a terrain from a point cloud.

import dtcc

# Load point cloud from LAS file
pointcloud = dtcc.load_pointcloud("data/helsingborg-residential-2022/pointcloud.las")

# Remove global outliers
pointcloud = pointcloud.remove_global_outliers(3.0)

# Build terrain
terrain = dtcc.builder.build_terrain_mesh(
    pointcloud=pointcloud,
    max_mesh_size=10,
    min_mesh_angle=25,
    smoothing=3,
)

# View mesh
terrain.mesh.view()
