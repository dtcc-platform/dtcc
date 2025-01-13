# Copyright (C) 2023 Dag Wästberg
# Licensed under the MIT License
#
# This demo illustrates how to generate a terrain mesh from a point cloud.

import dtcc
from pathlib import Path

# Set data paths
data_directory = (
    Path(__file__).parent.resolve() / "../data/helsingborg-residential-2022"
)
buildings_path = data_directory / "footprints.shp"
pointcloud_path = data_directory / "pointcloud.las"


pointcloud = dtcc.io.load_pointcloud(pointcloud_path)
pointcloud = pointcloud.remove_global_outliers(3.0)

# load footprints
footprints = dtcc.io.load_footprints(buildings_path, "uuid")

# merge and clean up footprints
merged_footprints = dtcc.builder.merge_building_footprints(
    footprints, lod=dtcc.model.GeometryType.LOD0, max_distance=0.5, min_area=10
)

simplifed_footprints = dtcc.builder.simplify_building_footprints(
    merged_footprints, 0.25, lod=dtcc.model.GeometryType.LOD0
)

clearance_fix = dtcc.builder.fix_building_footprint_clearance(simplifed_footprints, 0.5)


# extract footprint surfaces
footprints = [building.lod0 for building in clearance_fix]

# set subdomain resolution every other building to 2 and the rest to 0.5
subdomain_resolution = [0.5] * len(footprints)
for i in range(len(footprints)):
    if i % 2 == 0:
        subdomain_resolution[i] = 2


terrain = dtcc.builder.build_terrain_mesh(
    pointcloud,
    subdomains=footprints,
    subdomain_resolution=subdomain_resolution,
    max_mesh_size=20,
    min_mesh_angle=25,
    smoothing=3,
)

terrain.mesh.view()
