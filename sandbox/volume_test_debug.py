"""
This file aims to debug the volume meshing workflow 
(Polyggon merging/cleanup -> Spade surface mesh -> Tetgen volume mesh )

Tetgen breaks on certain input areas as input surface has self-intersections.

It copies much of the code from:
- dtcc_core.builder.geometry_builders.meshes.py
- dtcc/demos/build_city_volume_mesh.py
and adds debug plotting and output steps.
"""
from typing import Any, Dict, Optional
import numpy as np
import matplotlib.pyplot as plt

from dtcc_core.model import (
    Mesh,
    VolumeMesh,
    Building,
    Terrain,
    City,
    Surface,
    MultiSurface,
    GeometryType,
    PointCloud,
)

_LOD_PRIORITY: dict[GeometryType, int] = {
    GeometryType.LOD0: 0,
    GeometryType.LOD1: 1,
    GeometryType.LOD2: 2,
    GeometryType.LOD3: 3,
}

from dtcc_core.builder.model_conversion import (
    create_builder_polygon,
    create_builder_surface,
    create_builder_multisurface,
    builder_mesh_to_mesh,
    builder_volume_mesh_to_volume_mesh,
    mesh_to_builder_mesh,
    create_builder_city,
    raster_to_builder_gridfield,
)

from dtcc_core.builder import _dtcc_builder

from dtcc_core.builder.polygons.polygons import (
    polygon_merger,
    simplify_polygon,
    remove_slivers,
    fix_clearance,
)

from dtcc_core.builder.geometry_builders.buildings import (
    extract_roof_points,
    compute_building_heights,
)

from dtcc_core.builder.geometry_builders.terrain import (
    build_terrain_mesh,
    build_terrain_raster,
)

from dtcc_core.builder.building.modify import (
    merge_building_footprints,
    simplify_building_footprints,
    fix_building_footprint_clearance,
    clean_building_footprints,
)

from dtcc_core.builder.meshing.convert import mesh_to_raster

from dtcc.logging import debug, info, warning, error

from dtcc_core.builder.meshing.tetgen import (
    build_volume_mesh as tetgen_build_volume_mesh,
    get_default_tetgen_switches,
    is_tetgen_available,
)

import dtcc

def plot_boundaries(polygons):
    print("Plotting building footprint boundaries...")
    fig, ax = plt.subplots(figsize=(8, 8))

    for poly in polygons:
        # Exterior boundary
        x, y = poly.exterior.xy
        ax.plot(x, y, color="black")

        # Holes (interior rings)
        for interior in poly.interiors:
            x, y = interior.xy
            ax.plot(x, y, color="red")  # optional: distinguish holes

    ax.set_aspect("equal")
    ax.set_title("Building Footprint Boundaries")
    plt.show()

def build_city_volume_mesh(
    city: City,
    lod: GeometryType = GeometryType.LOD1,
    domain_height: float = 100.0,
    max_mesh_size: float = 10.0,
    merge_buildings: bool = True,
    boundary_face_markers: bool = True,
    tetgen_switches: Optional[Dict[str, Any]] = None,
    tetgen_switch_overrides: Optional[Dict[str, Any]] = None,
) -> VolumeMesh:
    """
    Build a 3D tetrahedral volume mesh for a city terrain with embedded building volumes.

    This function generates a ground mesh from the city terrain and extrudes building
    footprints to produce a full volume mesh, optionally merging adjacent buildings
    and marking boundary faces.

    Parameters
    ----------
    city : City
        City object containing terrain and building data. Terrain must have either
        a raster or mesh representation.
    lod : GeometryType, optional
        Level of detail for building footprints. Defaults to GeometryType.LOD1.
    domain_height : float, optional
        Height of the mesh domain above the terrain (in the same units as city coordinates).
        Defaults to 100.0.
    max_mesh_size : float, optional
        Maximum allowed mesh element size. Used both for ground mesh cell sizing
        and to cap subdomain resolutions. Defaults to 10.0.
    merge_buildings : bool, optional
        If True, merge adjacent building footprints into larger blocks before meshing.
        Defaults to True.
    boundary_face_markers : bool, optional
        If True, add integer markers to the boundary faces of the volume mesh as a
        post-processing step. Defaults to True. See Notes for marker conventions.
    tetgen_switches : dict, optional
        Optional TetGen switch parameters passed through to ``dtcc_wrapper_tetgen``.
        Provide keys as defined by ``dtcc_wrapper_tetgen.switches.DEFAULT_TETGEN_PARAMS``.
    tetgen_switch_overrides : dict, optional
        Optional low-level overrides forwarded to ``build_tetgen_switches`` for custom
        text-based switch assembly.

    Returns
    -------
    VolumeMesh
        A VolumeMesh instance representing the 3D tetrahedral mesh of the city domain, including
        building volumes.

    Raises
    ------
    ValueError
        If the city has no terrain data (neither raster nor mesh).
    ValueError
        If the terrain object exists but has no usable raster or mesh data.

    Boundary Face Markers
    ---------------------
    When `boundary_face_markers=True`, integer markers are added as follows (for
    a domain containing N buildings):

    - `0` to `N-1`:  Wall faces of the N buildings
    - `N` to `2*N-1`:  Roof faces of the N buildings
    - `-1`:  Ground (terrain) faces
    - `-2`:  Top faces of the volume domain
    - `-3`, `-4`, `-5`, `-6`:  The four vertical boundary faces of the domain

    Notes
    -----
    - Building footprints are extracted at the specified `lod` level (or LOD0 if
      `merge_buildings` is True), optionally merged and simplified using internal
      area/detail thresholds.
    - Subdomain resolution for each building is set to the minimum of its height
      and `max_mesh_size`.
    - Ground mesh is built via the internal DTCC builder, and building surfaces
      are extruded into the volume domain of height `domain_height`.
    - Mesh smoothing and quality parameters (angles, iterations, tolerances, aspect
      ratios) are applied internally.

    Examples
    --------
    >>> mesh = build_volume_mesh(my_city,
    ...                          lod=GeometryType.LOD1,
    ...                          domain_height=150.0,
    ...                          max_mesh_size=5.0,
    ...                          merge_buildings=False,
    ...                          boundary_face_markers=True)
    """

    # FIXME: Where do we set these parameters?
    min_building_area = 10.0
    min_building_detail = 0.5
    min_mesh_angle = 30.0

    # Fallback dtcc volume meshing parameters
    smoother_max_iterations = 5000
    smoothing_relative_tolerance = 0.005
    aspect_ratio_threshold = 10.0
    debug_step = 7

    buildings = city.buildings
    if not buildings:
        warning("City has no buildings.")

    if merge_buildings:
        info(f"Merging {len(buildings)} buildings...")
        merged_buildings = merge_building_footprints(
            buildings,
            GeometryType.LOD0,
            min_area=min_building_area,
        )

        smallest_hole = max(min_building_detail, min_building_detail**2)
        cleaned_footprints = clean_building_footprints(
            merged_buildings,
            clearance=min_building_detail,
            smallest_hole_area=smallest_hole,
        )

        merged_buildings = merge_building_footprints(
            cleaned_footprints,
            GeometryType.LOD0,
            max_distance=0.0,
            min_area=min_building_area,
        )

        simplifed_footprints = simplify_building_footprints(
            merged_buildings, min_building_detail / 2, lod=GeometryType.LOD0
        )

        building_footprints = [
            b.get_footprint(GeometryType.LOD0) for b in simplifed_footprints
        ]
        info(f"After merging: {len(building_footprints)} buildings.")
    else:
        building_footprints = [b.get_footprint(lod) for b in buildings]

    plot_boundaries([bf.to_polygon() for bf in building_footprints if bf is not None])
    # Set subdomain resolution to half the building height
    subdomain_resolution = [
        min(building.height, max_mesh_size) for building in buildings
    ]

    terrain = city.terrain
    if terrain is None:
        raise ValueError("City has no terrain data. Please compute terrain first.")
    terrain_raster = terrain.raster
    terrain_mesh = terrain.mesh
    if terrain_raster is None and terrain_mesh is None:
        raise ValueError("City terrain has no data. Please compute terrain first.")
    if terrain_raster is None and terrain_mesh is not None:
        terrain_raster = mesh_to_raster(terrain_mesh, cell_size=max_mesh_size)

    _surfaces = [
        create_builder_surface(footprint)
        for footprint in building_footprints
        if footprint is not None
    ]
    hole_surfaces: list = []
    lod_switch_value = _LOD_PRIORITY.get(lod, _LOD_PRIORITY[GeometryType.LOD3])
    meshing_directives = [lod_switch_value] * len(_surfaces)

    
    _dem = raster_to_builder_gridfield(terrain.raster)

    if is_tetgen_available():

        # FIXME: Where do we set these parameters?
        smoothing = 1
        merge_meshes = True
        sort_triangles = False
        max_edge_radius_ratio = None  # 1.414
        min_dihedral_angle = None  # 30.0
        max_tet_volume = 20.0

        builder_mesh = _dtcc_builder.build_city_surface_mesh(
            _surfaces,
            hole_surfaces,
            meshing_directives,
            subdomain_resolution,
            _dem,
            max_mesh_size,
            min_mesh_angle,
            smoothing,
            merge_meshes,
            sort_triangles,
        )

        surface_mesh = builder_mesh[0].from_cpp()

        # Surface mesh debug output
        surface_mesh.save("debug_city_surface_mesh.vtk")

        if surface_mesh.faces is None or len(surface_mesh.faces) == 0:
            raise ValueError("Surface mesh has no faces. Cannot build volume mesh.")
        if surface_mesh.markers is None or len(surface_mesh.markers) == 0:
            raise ValueError(
                "Surface mesh has no face markers. Cannot build volume mesh."
            )

        switches_params = get_default_tetgen_switches()
        if max_tet_volume is not None:
            switches_params["max_volume"] = max_tet_volume
        if max_edge_radius_ratio is not None or min_dihedral_angle is not None:
            switches_params["quality"] = (
                max_edge_radius_ratio,
                min_dihedral_angle,
            )
        if tetgen_switches:
            switches_params.update(tetgen_switches)

        info("Building volume mesh with TetGen...")
        volume_mesh = tetgen_build_volume_mesh(
            mesh=surface_mesh,
            build_top_sidewalls=True,
            top_height=domain_height,
            switches_params=switches_params,
            switches_overrides=tetgen_switch_overrides,
            return_boundary_faces=boundary_face_markers,
        )
        return volume_mesh

    # Convert from Python to C++
    _building_polygons = [
        create_builder_polygon(footprint.to_polygon())
        for footprint in building_footprints
        if footprint is not None
    ]
    # FIXME: Pass bounds as argument (not xmin, ymin, xmax, ymax).

    # Build ground mesh
    _ground_mesh = _dtcc_builder.build_ground_mesh(
        _building_polygons,
        [],
        subdomain_resolution,
        terrain.bounds.xmin,
        terrain.bounds.ymin,
        terrain.bounds.xmax,
        terrain.bounds.ymax,
        max_mesh_size,
        min_mesh_angle,
        True,
    )

    # FIXME: Should not need to convert from C++ to Python mesh.
    # Convert from Python to C++

    # Create volume mesh builder
    volume_mesh_builder = _dtcc_builder.VolumeMeshBuilder(
        _surfaces, _dem, _ground_mesh, domain_height
    )

    # FIXME: How do we handle parameters?
    # Build volume mesh
    _volume_mesh = volume_mesh_builder.build(
        smoother_max_iterations,
        smoothing_relative_tolerance,
        0.0,
        aspect_ratio_threshold,
        debug_step,
    )
    volume_mesh = _volume_mesh.from_cpp()

    if boundary_face_markers:
        boundary_face_markers = _dtcc_builder.compute_boundary_face_markers(
            _volume_mesh
        )
        if boundary_face_markers is not None:
            volume_mesh.boundary_markers = boundary_face_markers

    return volume_mesh

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == "__main__":
  # Define bounds (a residential area in Helsingborg)
  h = 500.0

  # Demo area
  bounds = dtcc.Bounds(319891 , 6399790 , 319891 + h, 6399790 + h)

  # Problematic area #1 
  bounds = dtcc.Bounds(319882, 6399450, 320173 +200, 6399740 +200)
  
# bounds = dtcc.Bounds(3.20451472e+05, 6.40042048e+06, 3.20451472e+05 + h, 6.40042048e+06 + h)
# bounds = dtcc.Bounds(319891 -h , 6399790 - h, 319891 + h, 6399790 + h)

  # Download pointcloud and building footprints
  pointcloud = dtcc.download_pointcloud(bounds=bounds)
  buildings = dtcc.download_footprints(bounds=bounds)

  # Remove global outliers
  pointcloud = pointcloud.remove_global_outliers(3.0)

  # Build terrain raster
  raster = dtcc.build_terrain_raster(pointcloud, cell_size=2, radius=3, ground_only=True)

  # Extract roof points and compute building heights
  buildings = dtcc.extract_roof_points(buildings, pointcloud)
  buildings = dtcc.compute_building_heights(buildings, raster, overwrite=True)

  # Create city and add geometries
  city = dtcc.City()
  city.add_terrain(raster)
  city.add_buildings(buildings, remove_outside_terrain=True)

  # Build city volume mesh
  domain_height = 80.0  # Height of the volume mesh domain
  max_mesh_size = 10.0  # Maximum size of the mesh triangles

  tetgen_switches = {
      "plc": True, 
      # "preserve_surface": True,
      "max_volume": max_mesh_size,
      "quality": None , #(None, None)
      # "detect_self_intersections": True,
      # "check_mesh": True,
      # "reconstruct": True,
      "extra": "-VVV" # Very verbose output for debugging
  }

  
  volume_mesh = build_city_volume_mesh(city, 
                                            merge_buildings=True,
                                            domain_height=domain_height, 
                                            max_mesh_size=max_mesh_size,
                                            tetgen_switches=tetgen_switches,
                                            boundary_face_markers=False)

  volume_mesh.save("debug_city_volume_mesh.vtk")