# TODO proper import like the rest, since dtcc-data is already imported in init.py
# TODO only import is dtcc
# TODO Remove auth from download_pointcloud
# TODO Add something regarding licensing in README.md for geotorget

from dtcc_atlas.atlas import download_roadnetwork, download_footprints, download_pointcloud, get_bounding_box
from shapely import box 

# NOTE: The server is still under the process of scraping all the data. Currently the server contains small portions of the whole dataset.

parameters = {}
parameters["username"] = ""
parameters["password"] = ""
parameters["cache_directory"] = ""

# Auth is happening against PAM of data2.dtcc.chalmers.se via SSHv2

# TODO: Add OSM/Google Maps footprints in case of non-authentication

# NOTE: WiP password key-chain and way for not using cleartext passwords.

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
