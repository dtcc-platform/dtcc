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
terrain_mesh = dtcc.builder.build_terrain_mesh(terrain_raster)

footprints = dtcc.builder.extract_roof_points(
    footprints, pc, statistical_outlier_remover=True
)
footprints = dtcc.builder.compute_building_heights(
    footprints, terrain_raster, overwrite=True
)

merged_footprints = dtcc.builder.merge_building_footprints(footprints, lod=dtcc.model.GeometryType.LOD0, max_distance=0.5, min_area=10)

merged_footprints = merged_footprints[63:65]

city = dtcc.City()
# city.add_terrain(terrain_mesh)
city.add_buildings(merged_footprints, remove_outside_terrain=False)

city.view()
