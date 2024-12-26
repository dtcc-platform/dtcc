# This demo illustrates how to load and view a point cloud.

import dtcc
from pathlib import Path

data_directory = Path(__file__).parent / ".." / "data" / "helsingborg-residential-2022"
pointcloud_path = data_directory / "pointcloud.las"
# Load point cloud from LAS file
pc = dtcc.load_pointcloud(pointcloud_path)

# View point cloud (color by z-coordinate)
color_data = pc.points[:, 2]
pc.view(data=color_data)
