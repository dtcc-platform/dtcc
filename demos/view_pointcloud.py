# This demo illustrates how to load and view a point cloud.

import dtcc

# Set data directory (and check that it exists)
data_directory = dtcc.set_data_directory("data/helsingborg-residential-2022")

# Load point cloud from LAS file
pc = dtcc.load_pointcloud(data_directory / "pointcloud.las")

# View point cloud (color by z-coordinate)
color_data = pc.points[:, 2]
pc.view(data=color_data)
