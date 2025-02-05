# Copyright (C) 2023 Dag Wästberg
# Licensed under the MIT License
#
# This demo illustrates how to generate a terrain mesh from a point cloud.

import dtcc

# Define the bounding box for the Helsingborg residential area. 
# These coordinates specify the area of interest to be passed into the 
bounds = dtcc.Bounds(
    xmin=319891,
    ymin=6399790,
    xmax=319891+2000,
    ymax=6399790+2000
)

pc = dtcc.download_data(data_type='lidar', provider='dtcc', user_bbox=bounds)
pointcloud = pc.remove_global_outliers(3.0)

# load footprints
footprints = dtcc.download_data(data_type='footprints', provider='OSM', user_bbox=bounds)

# merge and clean up footprints
merged_footprints = dtcc.merge_building_footprints(
    footprints, lod=dtcc.GeometryType.LOD0, max_distance=0.5, min_area=10
)

simplifed_footprints = dtcc.simplify_building_footprints(
    merged_footprints, 0.25, lod=dtcc.GeometryType.LOD0
)

clearance_fix = dtcc.fix_building_footprint_clearance(simplifed_footprints, 0.5)


# extract footprint surfaces
footprints = [building.lod0 for building in clearance_fix]

# set subdomain resolution every other building to 2 and the rest to 0.5
subdomain_resolution = [0.5] * len(footprints)
for i in range(len(footprints)):
    if i % 2 == 0:
        subdomain_resolution[i] = 2


terrain = dtcc.build_terrain_mesh(
    pointcloud,
    subdomains=footprints,
    subdomain_resolution=subdomain_resolution,
    max_mesh_size=20,
    min_mesh_angle=25,
    smoothing=3,
)

terrain.mesh.view()
