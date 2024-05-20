import dtcc
from pathlib import Path


data_directory = Path(__file__).parent / ".." / "data" / "cityjson"

city = dtcc.load_city(data_directory / "DenHaag_01.city.json")

print("City loaded, calculating bounds...")
bounds = city.bounds
print(bounds)


terrain = dtcc.builder.flat_terrain(city.bounds.zmin, city.bounds)
city.remove_terrain()
city.add_terrain(terrain)


surface_mesh = dtcc.builder.build_surface_mesh(city, dtcc.GeometryType.LOD2)

print("Done!")
surface_mesh.view()
