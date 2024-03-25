import dtcc

from pathlib import Path
import dtcc_viewer

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

lod1_buildings = dtcc.builder.build_lod1_buildings(
    footprints, default_ground_height=terrain_raster.min, always_use_default_ground=True
)
city = dtcc.City()
print(terrain_raster, type(terrain_raster))
city.add_terrain(terrain_raster)
city.add_buildings(lod1_buildings)

surface_mesh = dtcc.builder.build_surface_mesh(
    city, max_mesh_size=10, min_mesh_angle=25
)

surface_mesh.view()
