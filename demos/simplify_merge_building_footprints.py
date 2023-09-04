import dtcc

city = dtcc.io.load_city("../data/HelsingborgHarbour2022/PropertyMap.shp")

# Simplify building polygons by removing vertices so that the resulting polygon
# is within the given tolerance of the original polygon.
city = city.simplify_buildings(tolerance=0.5)

# merge buildings that are closer to each other than the given distance
city = city.merge_buildings(max_distance=0.5)

# remove small buildings
city = city.remove_small_buildings(min_area=15)

city.save("simplified_city.shp")
