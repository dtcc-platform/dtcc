# This demo illustrates how to build a terrain mesh from a point cloud.

import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

# Dowload point cloud and footprints
pointcloud = dtcc.download_pointcloud(bounds=bounds)
footprints = dtcc.download_footprints(provider="OSM", bounds=bounds)

# Remove global outliers
pointcloud = pointcloud.remove_global_outliers(3.0)

# FIXME: Rename merge_building_footprints --> merge_footprints etc

# Merge and clean footprints
footprints = dtcc.merge_building_footprints(
    footprints, lod=dtcc.GeometryType.LOD0, max_distance=0.5, min_area=10
)

footprints = dtcc.simplify_building_footprints(
    footprints, 0.25, lod=dtcc.GeometryType.LOD0
)

footprints = dtcc.fix_building_footprint_clearance(footprints, 0.5)

# Extract footprint surfaces
footprints = [building.lod0 for building in footprints]

# Set subdomain resolution every other building to 2 and the rest to 0.5
subdomain_resolution = [0.5] * len(footprints)
for i in range(len(footprints)):
    if i % 2 == 0:
        subdomain_resolution[i] = 2

# Build terrain mesh
mesh = dtcc.build_terrain_mesh(
    pointcloud,
    subdomains=footprints,
    subdomain_resolution=subdomain_resolution,
    max_mesh_size=20,
    min_mesh_angle=25,
    smoothing=3,
)

# View terrain mesh
mesh.view()
