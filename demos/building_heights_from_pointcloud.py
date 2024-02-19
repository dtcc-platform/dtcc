#!/usr/bin/env python3

# import dtcc
# from dtcc import builder
# from dtcc import io
import dtcc_io as io
import dtcc_builder as builder
from pathlib import Path


# Set data paths
data_directory = Path(__file__).parent / ".." / "data/helsingborg-residential-2022"
footprints_path = data_directory / "footprints.shp"
pointcloud_path = data_directory

### set heights of buildings from a point cloud

# load pointcloud and footprints
pc = io.load_pointcloud(pointcloud_path)
cm = io.load_footprints(footprints_path)

# clenup pointcloud
pc = pc.remove_global_outliers(3)

# set terrain
cm = cm.terrain_from_pointcloud(pc, cell_size=1, radius=3, ground_only=True)

# set building heights
cm = builder.city_methods.compute_building_points(cm, pc)

# set building heights
city = builder.city_methods.compute_building_heights(cm, min_building_height=2.5)

io.save_city(city, data_directory / "city_with_heights.shp")
