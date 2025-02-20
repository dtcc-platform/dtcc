# This demo illustrates how to build a mesh for a CityJSON city model.

import dtcc
from urllib.request import urlretrieve

# Download example CityJSON file
base = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/"

# 3-20-DELFSHAVEN.city.json: ValueError: City terrain has no data. Please compute terrain first.
# 9-284-556.city.json: ValueError: Unknown geometry type: LOD1.2
# DA13_3D_Buildings_Merged.city.json: City terrain has no data. Please compute terrain first.
# DenHaag_01.city.json: Works but occasional Triangle error on CI
# Ingolstadt.city.json: TypeError: Geometry array should be of object dtype
# LoD3_Railway.city.json: TypeError: Geometry array should be of object dtype
# VM05_2009.city.json: ValueError: City terrain has no data. Please compute terrain first.
# Vienna_102081.city.json: ValueError: City terrain has no data. Please compute terrain first.
# Zurich_Building_LoD2_V10.city.json: Hangs (or takes a really long time)
# geoRES_testdata_v1.0.0.city.json: TypeError: Geometry array should be of object dtype

# url = base + "3-20-DELFSHAVEN.city.json"
url = base + "geoRES_testdata_v1.0.0.city.json"

urlretrieve(url=url, filename="city.json")

# Load city model from CityJSON file
city = dtcc.load_city("city.json")

# Build city mesh
mesh = dtcc.build_city_mesh(city, dtcc.GeometryType.LOD2)

# View mesh
mesh.view()
