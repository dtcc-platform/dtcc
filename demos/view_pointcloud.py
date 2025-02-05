# This demo illustrates how to load and view a point cloud.

import dtcc

# Define the bounding box for the Helsingborg residential area. 
# These coordinates specify the area of interest to be passed into the 
bounds = dtcc.Bounds(
    xmin=319891,
    ymin=6399790,
    xmax=319891+2000,
    ymax=6399790+2000
)

pc = dtcc.download_data(data_type='lidar', provider= 'dtcc', user_bbox=bounds)

# View point cloud (color by z-coordinate)
color_data = pc.points[:, 2]
pc.view(data=color_data)
