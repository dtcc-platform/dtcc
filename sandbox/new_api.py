from dtcc import *

# Loading a city from internal format (Protobuf)
city = load_city("city.pb")

# Loading a city from CityJSON
city = load_city("city.json")

# Building a city from raw data
footprints = load_footprints("footprints.shp")  # [Polygon]
pointcloud = load_pointcloud("pointcloud.las")  # PointCloud
city = City()
city.build_geometry(footprints, pointcloud, lod=LOD1)

# Building mesh
city.build_mesh(lod=LOD1)  # Builds mesh for a specific LOD
city.build_meshes()  # Builds meshes for all available LODs
