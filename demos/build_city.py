import dtcc

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

city = dtcc.City()
city.bounds = bounds

city.download_footprints()
city.download_pointcloud()

city.build_terrain(
    cell_size=2.0,
    build_mesh=True,
    max_triangle_size=5.0,
    smoothing=3,
)

city.build_lod1_buildings()

# View city
city.view()
