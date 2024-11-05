# TODO proper import like the rest, since dtcc-data is already imported in init.py
# TODO only import is dtcc
# TODO Remove auth from download_pointcloud
# TODO Add something regarding licensing in README.md for geotorget

# from dtcc_atlas.atlas import download_roadnetwork, download_footprints, download_pointcloud, get_bounding_box
import dtcc


# NOTE: The server is still under the process of scraping all the data. Currently the server contains small portions of the whole dataset.

parameters = dtcc.data.parameters.default()
parameters["username"] = "" 
parameters["password"] = "" 
parameters["cache_directory"] = ""

"""Start local server to serve the map page"""
dtcc.data.atlas.start_server()
try:
    data = dtcc.data.atlas.serve_map()
    xmin = data['topLeft']['lng']
    xmax = data['bottomRight']['lng']

    ymin = data['bottomRight']['lat']
    ymax = data['topLeft']['lat']

    # Auth is happening against PAM of data2.dtcc.chalmers.se via SSHv2

    # TODO: Add OSM/Google Maps footprints in case of non-authentication

    # NOTE: WiP password key-chain and way for not using cleartext passwords.

    # Create the initial bounding box to request the data

    bbox_gpkg = dtcc.model.Bounds(xmin=xmin,
                                  ymin=ymin,
                                  xmax=xmax,
                                  ymax=ymax)

    bbox_laz = dtcc.model.Bounds(xmin=xmin,
                                 ymin=ymin,
                                 xmax=xmax,
                                 ymax=ymax)

    # Downloads all missing Lidar files for the specified bounding box and updates/creates the lidar atlas
    if 'pointCloudLaz' in data['selectedOptions']:
        dtcc.data.download_pointcloud(bbox_laz, parameters)

    # Downloads all missing GPKG files for footprints for the specified bounding box
    if 'footprintsGpkg' in data['selectedOptions']:
        dtcc.data.download_footprints(bbox_gpkg, parameters)

    # Downloads all missing Lidar files for roadnetwork for the specified bounding box
    if 'roadNetworkGpkg' in data['selectedOptions']:
        dtcc.data.download_roadnetwork(bbox_gpkg, parameters)

except Exception as ex:
    print(f"DTCC Data Demo had an exception: {ex}")

finally:
    """Stop local server"""
    print("Server is stopping")
    dtcc.data.atlas.stop_server()
    print("Server stopped")

# Commented for CI. Opens a map that the user can draw a bounding box. returns the coordinates of the bounding box
"""Disable the old way, but keeping it for testing, or faster revert."""
# print(dtcc.data.get_bounding_box())
