from time import time
import numpy as np

from dtcc import *
from vertex_extractor import extract_vertices

# This should not be needed
from dtcc_model.object.object import GeometryType

city = load_cityjson("DenHaag_01.city.json")

# Option A: Python iteration and numpy.concatenate
t = time()
vertices = np.empty((0, 3))
for building in city.buildings:
    for building_part in building.building_parts:
        multi_surface = building_part.geometry[GeometryType.LOD2]
        for surface in multi_surface.surfaces:
            vertices = np.concatenate((vertices, surface.vertices), axis=0)
# print(np.shape(vertices), vertices[-1, :])
dt = time() - t
print(f"A: {dt: .3g} s")

# Option B: Python iteration and appending to a list
t = time()
vertices = []
for building in city.buildings:
    for building_part in building.building_parts:
        multi_surface = building_part.geometry[GeometryType.LOD2]
        for surface in multi_surface.surfaces:
            vertices.extend(surface.vertices)
vertices = np.array(vertices)
# print(np.shape(vertices), vertices[-1, :])
dt = time() - t
print(f"B: {dt: .3g} s")

# Option C: Cython
t = time()
vertices = extract_vertices(city)
# print(np.shape(vertices), vertices[-1, :])
dt = time() - t
print(f"C: {dt: .3g} s")
