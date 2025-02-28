# This demo illustrates how download data with different providers.

import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

# Download point cloud (lidar) data using default provider (DTCC)
pointcloud = dtcc.download_pointcloud(bounds=bounds)

# Download footprint data using default provider (DTCC)
footprints_dtcc = dtcc.download_footprints(bounds=bounds)

# Download footprint data using OSM provider
footprints_osm = dtcc.download_footprints(bounds=bounds, provider="OSM")

# Download road network data using OSM provider
roadnetwork_osm = dtcc.download_roadnetwork(bounds=bounds, provider="OSM")

# Clear cache of downloaded data
dtcc.empty_cache()
