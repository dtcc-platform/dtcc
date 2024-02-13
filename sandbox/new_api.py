from dtcc import *

# Load city from internal format (Protobuf)
city = load_city("city.pb")

# Load city from CityJSON
city = load_city("city.json")

# Build city from raw data
footprints = load_footprints("footprints.shp")  # [Polygon]
pointcloud = load_pointcloud("pointcloud.las")  # PointCloud
city = City()
city.build_geometry(footprints, pointcloud, lod=LOD1)

# Build meshes(es)
city.build_mesh(lod=LOD1)  # Builds mesh for a specific LOD
city.build_meshes()  # Builds meshes for all available LODs

# Build volume mesh(es)
city.build_volume_mesh(lod=LOD1)  # Builds volume mesh for a specific LOD
city.build_volume_meshes()  # Builds volume meshes for all available LODs
