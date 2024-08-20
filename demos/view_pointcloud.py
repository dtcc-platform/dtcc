# This demo illustrates how to load and view a point cloud.

import dtcc

# Load point cloud from LAS file
pc = dtcc.load_pointcloud("data/helsingborg-residential-2022/pointcloud.las")

# View point cloud (color by z-coordinate)
color_data = pc.points[:, 2]
pc.view(data=color_data)
