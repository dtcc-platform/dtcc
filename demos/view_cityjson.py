# This demo illustrates how to load and view a CityJSON city model.

import dtcc

# Set data directory (and check that it exists)
data_directory = dtcc.set_data_directory("data/cityjson")

# Load city model from CityJSON file
city = dtcc.load_city(data_directory / "DenHaag_01.city.json")

# View city
city.view()
