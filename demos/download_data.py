import dtcc

#Demos showcasing how to use dtcc in order to fetch data with different providers
bounds = dtcc.Bounds(
    xmin=319891,
    ymin=6399790,
    xmax=319891+2000,
    ymax=6399790+2000
)

#For all functions the Default provider is dtcc
#Fetching Lidar data. Provider is dtcc. (Currently the only one, default)
pc = dtcc.download_pointcloud(bounds = bounds)

#Fetching Footprint data. Provider is dtcc (default)
footprints_dtcc = dtcc.download_footprints(bounds = bounds)

#Fetching Footprint data with another provider, OSM
footprints_osm = dtcc.download_footprints(bounds = bounds, provider="OSM")

#Fetching Roadnetwork data with OSM provider. (Currently the only one)
roadnetwork_osm = dtcc.download_roadnetwork(bounds = bounds, provider="OSM")

#Clearing the cache of downloaded data
dtcc.empty_cache()
