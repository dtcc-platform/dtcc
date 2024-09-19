from dtcc_atlas.atlas import download_roadnetwork, download_footprints, download_pointcloud, get_bounding_box
from shapely import box 

# NOTE: The server is still under the process of scraping all the data. Currently the server contains only a small portion of the whole dataset.
# That means that the area that the server can return is still minimal. 
parameters = {}
parameters["username"] = ""
parameters["password"] = ""
parameters["default_directory"] = ""
# Create the initial bounding box to request the data
bbox_gpkg = box(445646,7171055, 458746,7195055)
bbox_laz = box(300000,6500000, 302500,6505000)

# Downloads all missing Lidar files for the specified bounding box and updates/creates the lidar atlas

download_pointcloud(bbox_laz, parameters)

# Downloads all missing GPKG files for footprints for the specified bounding box 

download_footprints(bbox_gpkg, parameters)

# Downloads all missing Lidar files for roadnetwork for the specified bounding box 

download_roadnetwork(bbox_gpkg, parameters)

# Commented for CI. Opens a map that the user can draw a bounding box. returns the coordinates of the bounding box
# print(get_bounding_box())