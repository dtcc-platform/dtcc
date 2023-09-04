#!/usr/bin/env python3

import dtcc
from pathlib import Path
from dtcc import builder

data_dir = Path(__file__).parent / ".." / "data" / "HelsingborgResidential2022"

### set heights of buildings from a point cloud

# load pointcloud and footprints
pc = dtcc.io.load_pointcloud(data_dir / "PointCloud.las")
cm = dtcc.io.load_footprints(data_dir / "PropertyMap.shp")

# clenup pointcloud
pc = pc.remove_global_outliers(3)

# set terrain
cm = cm.terrain_from_pointcloud(pc, cell_size=1, radius=3, ground_only=True)

# set building heights
cm = builder.city_methods.compute_building_points(cm, pc)

# set building heights
city = builder.city_methods.compute_building_heights(cm, min_building_height=2.5)

dtcc.io.save_city(city, "city_with_heights.shp")
