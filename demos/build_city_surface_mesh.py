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


city = dtcc.load_city(filename)


print("City loaded, calculating bounds...")
bounds = city.bounds
print(bounds)


surface_mesh = dtcc.builder.build_surface_mesh(
    city, dtcc.GeometryType.LOD2, max_mesh_size=15, building_mesh_triangle_size=5
)

print("Done!")
surface_mesh.view()
