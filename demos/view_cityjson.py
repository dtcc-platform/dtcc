# This demo illustrates how to load and view a CityJSON city model.

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

# View city
city.view()

# Clean up
temp_path.close()
os.unlink(temp_path.name)
