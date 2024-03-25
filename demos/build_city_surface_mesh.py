import dtcc
from pathlib import Path


data_directory = Path(__file__).parent / ".." / "data" / "cityjson"

city = dtcc.load_city(data_directory / "DA13_3D_Buildings_Merged.city.json")

terrain = dtcc.builder.flat_terrain(0, city.bounds)
city.add_terrain(terrain)

surface_mesh = dtcc.builder.build_surface_mesh(city, dtcc.GeometryType.LOD2)

print("Done!")
surface_mesh.view()
