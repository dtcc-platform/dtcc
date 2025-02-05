# This demo illustrates how to load and view a CityJSON city model.

import dtcc

from pathlib import Path
from urllib.request import urlretrieve

# Fetch an example CityJSON file from the CityJSON organization datasets.
#
# The CityJSON organization provides various example datasets at:
# https://www.cityjson.org/datasets/
#
# In this demo, we download the 'DenHaag_01.city.json' file, which contains
# CityJSON data for The Hague (Den Haag). This file is fetched from a specific
# URL and saved locally for further processing.

filename = Path(__file__).parent/ "DenHaag_01.city.json"


# Download the CityJSON file from the provided URL and save it to 'filename'.
urlretrieve(url = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/DenHaag_01.city.json",
            filename= filename )

# Load city model from CityJSON file
city = dtcc.load_city(filename)

# View city
city.view()
