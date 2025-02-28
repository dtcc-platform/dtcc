# This demo illustrates how to build a mesh for a CityJSON city model.

import dtcc
from urllib.request import urlretrieve

# Download example CityJSON file
url = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/3-20-DELFSHAVEN.city.json"
urlretrieve(url=url, filename="city.json")

# Load city model from CityJSON file
city = dtcc.load_city("city.json")

# Add terrain if not present
if not city.has_terrain():
    city.add_flat_terrain(buffer=10)

# Build city mesh
mesh = dtcc.build_city_mesh(city, dtcc.GeometryType.LOD2)

# View mesh
mesh.view()
