# This demo illustrates how to build a city mesh from a point cloud and footprints.

import dtcc

city = dtcc.City()

h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h, 0, 200)
city.bounds = bounds

# Download pointcloud and building footprints
city.download_pointcloud(bounds=bounds, filter_on_z_bounds=True)
city.download_footprints(bounds=bounds)

city.building_heights_from_pointcloud()
surface_mesh = city.build_city_surface_mesh()

# View mesh
surface_mesh.view()
