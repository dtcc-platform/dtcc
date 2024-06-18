# This demo illustrates how to load and view a CityJSON city model.

import dtcc

# Load city model from CityJSON file
city = dtcc.load_city("data/cityjson/DenHaag_01.city.json")

# View city
city.view()
