from pathlib import Path
import dtcc

# Build a mesh from raw data
data_directory = Path("../data/helsingborg-residential-2022")
p = dtcc.builder.parameters.default()
p["data_directory"] = data_directory
p["mesh_resolution"] = 30.0
p["domain_height"] = 75.0
dtcc.builder.build(p)

buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory

origin, bounds = dtcc.builder.calculate_bounds(buildings_path, pointcloud_path, p)
city = dtcc.io.load_city(buildings_path, bounds=bounds)
pointcloud = dtcc.io.load_pointcloud(pointcloud_path, bounds=bounds)

# Build a city
city = dtcc.builder.build_city(city, pointcloud, bounds, p)

# From the city build meshes
volume_mesh, boundary_mesh = dtcc.builder.build_volume_mesh(city)

boundary_mesh.view(pc=pointcloud)
