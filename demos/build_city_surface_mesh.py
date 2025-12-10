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

lod = [dtcc.model.GeometryType.LOD1 for _ in city.buildings]
surface_mesh = city.build_surface_mesh(lod=lod,
                                       treat_lod0_as_holes= False)

# View mesh
surface_mesh.view()
