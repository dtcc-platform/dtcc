# This demo illustrates how to build a terrain mesh that conforms to building footprints.

import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

# Download point cloud and footprints
pointcloud = dtcc.download_pointcloud(bounds=bounds)
buildings = dtcc.download_footprints(bounds=bounds, provider="OSM")

# Remove global outliers
pointcloud = pointcloud.remove_global_outliers(3.0)

# Simplify building footprints
buildings = dtcc.merge_building_footprints(buildings, max_distance=0.5, min_area=10)
buildings = dtcc.simplify_building_footprints(buildings, tolerance=0.25)
buildings = dtcc.fix_building_footprint_clearance(buildings, 0.5)

# Extract footprints
footprints = [building.lod0 for building in buildings]

# Set subdomain resolutions to 2.0 for half of the buildings and 0.5 for the other half
subdomain_resolution = [2.0] * len(footprints)
subdomain_resolution[1::2] = [0.5] * len(subdomain_resolution[1::2])

# Build terrain mesh with footprints as subdomains
mesh = dtcc.build_terrain_mesh(
    pointcloud,
    subdomains=footprints,
    subdomain_resolution=subdomain_resolution,
    max_mesh_size=10,
    min_mesh_angle=25,
    smoothing=3,
)

# View terrain mesh
mesh.view()
