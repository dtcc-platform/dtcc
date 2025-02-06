# This demo illustrates how to load and view a CityJSON city model.

import dtcc
from urllib.request import urlretrieve

# Download example CityJSON file https://www.cityjson.org/datasets/s
url = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/DenHaag_01.city.json"
urlretrieve(url=url, filename="city.json")

# Load city model from CityJSON file
city = dtcc.load_city("city.json")

# View city
city.view()
