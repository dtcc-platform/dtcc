# This demo illustrates...

import dtcc
from urllib.request import urlretrieve

# Download example CityJSON file https://www.cityjson.org/datasets/s
url = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/DenHaag_01.city.json"
urlretrieve(url=url, filename="city.json")

# Load city model from CityJSON file
city = dtcc.load_city("city.json")

bounds = city.bounds

mesh = dtcc.build_surface_mesh(
    city, dtcc.GeometryType.LOD2, max_mesh_size=15, building_mesh_triangle_size=5
)

mesh.view()
