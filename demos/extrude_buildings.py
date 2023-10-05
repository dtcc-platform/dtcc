import dtcc
from pathlib import Path

# generate city_with_heights.shp by running demos/building_heights_from_pointcloud.py
# or load a shp file with a building height field

data_directory = Path("./dtcc-demo-data/helsingborg-residential-2022")

city = dtcc.io.load_city(data_directory / "city_with_heights.shp", height_field="height")

# estimate number of floors
for building in city.buildings:
    building.floors = max(1, int(round(building.height / 3)))

city = dtcc.builder.city_methods.extrude_buildings(
    city, mesh_resolution=5, zero_ground=True, cap_base=True
)
# the building.mesh field now contains a mesh for each building

# export each building as a separate obj file
out_dir = Path(data_directory / "building_meshes")
out_dir.mkdir(exist_ok=True)
for building in city.buildings:
    building_mesh = out_dir / f"{building.uuid}.obj"
    dtcc.io.save_mesh(building.mesh, building_mesh)
