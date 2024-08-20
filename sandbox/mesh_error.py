#!/usr/bin/env python3

import dtcc
from pathlib import Path
from dtcc import builder
from dtcc_model.geometry import Bounds

p = dtcc.parameters.default()
p["outlier_margin"] = 3.0
p["ransac_outlier_remover"] = False
p["statistical_outlier_remover"] = False

# Create a bounds object from unreal tiles workflow
bounds = Bounds()
bounds.xmin = 318066.99999999994
bounds.ymin = 6398483.000000002
bounds.xmax = 319000.99999999994
bounds.ymax = 6399413.000000002
# Set data paths
data_directory = Path(__file__).parent / ".." / "data/gothenburg_majorna"
footprints_path = data_directory / "Building Footprints" / "by_14.shp"
pointcloud_path = data_directory / "Lidar" / "09B002_639_31_7575.laz"

### set heights of buildings from a point cloud

# load pointcloud and footprints
pc = dtcc.io.load_pointcloud(pointcloud_path, bounds=bounds)
cm = dtcc.io.load_footprints(footprints_path, bounds=bounds)

# city = dtcc.build_city(cm, pc, bounds, p)
# surface_mesh = dtcc.build_city_surface_mesh(city, p)
# surface_mesh.view(pc=pc)
# exit()

# clenup pointcloud
# pc = pc.remove_global_outliers(5)
# pc = pc.remove_vegetation()
# print(f"pc min z: {pc.points[:, 2].min()}")
# print(f"pc max z: {pc.points[:, 2].max()}")

# pc.view()
# exit()
# set terrain
cm = cm.terrain_from_pointcloud(pc, cell_size=1, radius=3, ground_only=True)
# set building heights

cm = builder.city_methods.compute_building_points(cm, pc)

# set building heights
city = builder.city_methods.compute_building_heights(cm, min_building_height=2.5)

cm = builder.city_methods.compute_building_points(cm, pc)
cm = builder.city_methods.compute_building_heights(cm)
print(f"terrain maxbuild: {cm.terrain.data.max()}")
cm.view()
# for b in cm.buildings:
#     print(b.ground_level)
ground_mesh = builder.meshing.terrain_mesh(cm, 5.0, 20, smoothing=3)
surface_mesh = builder.build_city_surface_mesh(
    cm,
    p,
)
# print(f"Ground mesh: {ground_mesh}")
surface_mesh.view(pc=pc)
# set building heights
city = builder.city_methods.compute_building_heights(cm, min_building_height=2.5)
for b in city.buildings:
    if b.ground_level == 0:
        print(b.height, b.ground_level)
# dtcc.io.save_city(city, data_directory / "city_with_heights.shp")
