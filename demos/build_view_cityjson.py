# This demo illustrates how to view a CityJSON file as city model.

import dtcc
import numpy as np
from urllib.request import urlretrieve

# Download example CityJSON file
url1 = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/DenHaag_01.city.json"

url2 = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/Zurich_Building_LoD2_V10.city.json"

# Explore the two URLs above to see the difference between two models.
urlretrieve(url=url1, filename="city.json")

# Load city model from CityJSON file
city = dtcc.load_city("city.json")

# Add random attributes to buildings
building_year = [1900, 1920, 1940, 1960, 1980, 2000, 2020]
residents = np.arange(10) + 5

for i, building in enumerate(city.buildings):
    building.attributes["number residents"] = residents[i % len(residents)]
    building.attributes["construction year"] = building_year[i % len(building_year)]

# View mesh
city.view()

# VIEWING OPTIONS:
# Click buildings with LMB to see attributes in the data tab.
# When an object is selected, press 'z' to 'z'oom to the selected object.
# Press 'x' to set camarea to view the e'x'tent of the entire model.
# In Right side menu 'Controls' click -> Model -> Buildings, use UI components to::
# - Select data to color the buildings by.
# - Select colormap 'cmap'.
# - Set range for values to color by with sliders.
# If the model has terrain, explore tearrain viewing options in next drop down menu.
