import dtcc
from pathlib import Path


data_directory = Path(__file__).parent / ".." / "data" / "HelsingborgResidential2022"
buildings_path = data_directory / "PropertyMap.shp"
pointcloud_path = data_directory / "PointCloud.las"

footprints = dtcc.io.load_footprints(buildings_path, "uuid")

pc = dtcc.io.load_pointcloud(pointcloud_path)
pc = pc.remove_global_outliers(3)

terrain_raster = dtcc.builder.build_terrain_raster(
    pc, cell_size=2, radius=3, ground_only=True
)

footprints = dtcc.builder.extract_roof_points(
    footprints, pc, statistical_outlier_remover=True
)
footprints = dtcc.builder.compute_building_heights(
    footprints, terrain_raster, overwrite=True
)

merged_footprints = dtcc.builder.merge_building_footprints(
    footprints, lod=dtcc.model.GeometryType.LOD0, max_distance=0.5, min_area=10
)
simplifed_footprints = dtcc.builder.simplify_building_footprints(
    merged_footprints, 0.25, lod=dtcc.model.GeometryType.LOD0
)
clearance_fix = dtcc.builder.fix_building_footprint_clearance(simplifed_footprints, 0.5)


max_wall_length = [building.height for building in clearance_fix]


split_walls = dtcc.builder.split_footprint_walls(
    clearance_fix, max_wall_length=max_wall_length
)

meshes = []

i = 0
for building, tri_size in zip(split_walls, max_wall_length):
    print(f"Building {i} or {len(split_walls)}")
    if i == 335:
        problem_building = building.lod0.mesh()
        break
    else:
        i += 1
        continue
    meshes.append(building.lod0.mesh(tri_size))
    i += 1

# merged_mesh = dtcc.builder.meshing.merge_meshes(meshes)
print(problem_building)
problem_building.view()
# merged_footprints = merged_footprints[63:66]


# city = dtcc.City()
# # # city.add_terrain(terrain_mesh)
# city.add_buildings(split_walls)
# #
# #
# city.view()
