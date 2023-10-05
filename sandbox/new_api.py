from dtcc import *

# Load stuff
footprints = load_footprints("footprints.shp")
pointcloud = load_pointcloud("pointcloud.las")

# Build stuff
terrain = build_terrain(pointcloud)
buildings = build_buildings(footprints, pointcloud)

# Create city
city = City()
city.terrain = terrain
city.buildings = buildings

# Alternative
city = City(terrain, buildings)

# Shortcut (builds and sets data)
city = build_city(footprints, pointcloud)

# How to handle roads?
# How to handle trees?
# How to handle water?
