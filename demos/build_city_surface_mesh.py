import dtcc
from pathlib import Path


data_directory = Path(__file__).parent / ".." / "data" / "cityjson"

city = dtcc.load_city(data_directory / "DenHaag_01.city.json")

print("City loaded, calculating bounds...")
bounds = city.bounds
print(bounds)


surface_mesh = dtcc.builder.build_surface_mesh(
    city, dtcc.GeometryType.LOD2, max_mesh_size=15, building_mesh_triangle_size=5
)

print("Done!")
surface_mesh.view()
