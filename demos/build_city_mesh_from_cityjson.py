# This demo illustrates how to build a mesh for a CityJSON city model.

import dtcc
from urllib.request import urlretrieve
import tempfile
import os

# Download example CityJSON file
url = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/DenHaag_01.city.json"
temp_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
urlretrieve(url=url, filename=temp_path.name)

# Load city model from CityJSON file
city = dtcc.load_city(temp_path.name)


# Build city mesh
mesh = dtcc.build_city_mesh(city, dtcc.GeometryType.LOD2)

# View mesh
mesh.view()
os.unlink(temp_path.name)
