# This demo illustrates how to download and view a point cloud.

import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

# Download point cloud
pointcloud = dtcc.download_pointcloud(bounds=bounds)

# View point cloud (color by z-coordinate)
color_data = pointcloud.points[:, 2]
pointcloud.view(data=color_data)
