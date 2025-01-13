# This demo illustrates how to build a terrain from a point cloud.

import dtcc
from pathlib import Path

# Load point cloud from LAS file

data_directory = Path(__file__).parent / ".." / "data" / "helsingborg-residential-2022"
pointcloud_path = data_directory / "pointcloud.las"
pointcloud = dtcc.load_pointcloud(pointcloud_path)

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
