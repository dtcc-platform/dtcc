import json
from dtcc_model import dtcc_test_pb2 as proto
import dtcc
import numpy as np

from pathlib import Path

from time import time
from timeit import timeit


cj_file = Path("../data/cityjson/DA13_3D_Buildings_Merged.city.json")
# cj_file = Path("../data/cityjson/DenHaag_01.city.json")
# pb_file = Path("bm1.pb")

start_time = time()
c = dtcc.load_cityjson(cj_file)
print(f"loading cityjson took {time()-start_time} seconds")

start_time = time()

pb_city = proto.City()
buildings = c.buildings
pb_buildings = []
for b in buildings:
    pb_building = proto.Building()
    pb_building.id = b.id
    pb_building_geometry = []
    for g in b.lod2.surfaces:
        pb_geometry = proto.Surface()
        pb_geometry.vertices.extend(g.vertices.flatten())
        pb_building_geometry.append(pb_geometry)
    pb_building.geometry.extend(pb_building_geometry)
    pb_buildings.append(pb_building)
pb_city.buildings.extend(pb_buildings)
print(f"creating pb city took {time()-start_time} seconds")

test_pb_file = Path("dtcc_test_city.pb")

with open(test_pb_file, "wb") as f:
    f.write(pb_city.SerializeToString())

start_time = time()
city = proto.City.FromString(test_pb_file.read_bytes())
print(f"loading pb city took {time()-start_time} seconds")
