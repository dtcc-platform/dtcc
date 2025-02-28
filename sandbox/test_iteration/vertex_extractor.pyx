import numpy as np
cimport numpy as cnp
from dtcc_model.object.object import GeometryType

def extract_vertices(city):
    cdef list all_vertices = []
    cdef cnp.ndarray[cnp.float64_t, ndim=2] surface_vertices

    for building in city.buildings:
        for building_part in building.building_parts:
            multi_surface = building_part.geometry[GeometryType.LOD2]
            for surface in multi_surface.surfaces:
                surface_vertices = surface.vertices
                all_vertices.append(surface_vertices)

    return np.vstack(all_vertices)
