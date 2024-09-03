# Copyright (C) 2023 Sanjay Somanath
# Licensed under the MIT License
# This script documents the workflow for Sanjay.
# https://github.com/dtcc-platform/dtcc/issues/54
# Refactored to work with pip by Daniel Soljie

# Standard library imports
import numpy as np
import logging
from fnmatch import translate
from pathlib import Path
from typing import Tuple, List
from meshio import Mesh

import dtcc_io as io
from dtcc_model import Building,MultiSurface
from dtcc_builder.meshing import mesh_multisurfaces,merge_meshes
from dtcc import (
    Bounds,
    City,
    PointCloud,
    parameters,
    load_footprints,
    load_pointcloud,
    build_terrain_raster,
    build_lod1_buildings,
    # build_city,
    # build_building_meshes,
    # build_terrain_mesh,
    build_surface_mesh,
    save_mesh
    )

# ================= INTERNAL CONFIGURATION =======================
# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Unreal_Building_Generator')
info = logger.info


# ========== TEMP BUILDER REPLACEMENT FUNCTIONS ==================

def calculate_bounds(
    buildings_path, pointcloud_path, p: dict = None
) -> Tuple[Tuple[float, float], Bounds]:
    """
    Compute the domain bounds based on building footprints and pointcloud data.

    Parameters
    ----------
    `buildings_path` : str
        Path to the building footprints file.
    `pointcloud_path` : str
        Path to the point cloud data.
    `parameters` : dict, optional
        A dictionary of parameters for the computation, by default None.

    Returns
    -------
    `origin` : Tuple[float, float]
        Tuple containing the origin coordinates.
    `bounds` : dtcc_model.Bounds
    Tuple[Tuple[float, float], dtcc_model.Bounds]
        The computed domain bounds.

    """

    # Get parameters
    p = p or parameters.default()

    # Compute domain bounds automatically or from parameters
    if p["auto_domain"]:
        info("Calculating domain bounds automatically...")
        city_bounds = io.footprints.building_bounds(buildings_path, p["domain_margin"])
        info(f"Footprint bounds: {city_bounds}")
        pointcloud_bounds = io.pointcloud.calc_las_bounds(pointcloud_path)
        info(f"Point cloud bounds: {pointcloud_bounds}")
        city_bounds.intersect(pointcloud_bounds)
        info(f"Intersected bounds: {city_bounds}")
        bounds = city_bounds.tuple
        origin = bounds[:2]
        p["x0"] = origin[0]
        p["y0"] = origin[1]
        p["x_min"] = 0.0
        p["y_min"] = 0.0
        p["x_max"] = bounds[2] - bounds[0]
        p["y_max"] = bounds[3] - bounds[1]
    else:
        info("Calculating domain bounds from parameters...")
        origin = (p["x0"], p["y0"])
        bounds = (
            p["x0"] + p["x_min"],
            p["y0"] + p["y_min"],
            p["x0"] + p["x_max"],
            p["y0"] + p["y_max"],
        )

    # Set bounds
    bounds = Bounds(
        xmin=bounds[0],
        ymin=bounds[1],
        xmax=bounds[2],
        ymax=bounds[3],
    )

    return origin, bounds



def build_city(
    buildings: List[Building],
    point_cloud: PointCloud,
    bounds: Bounds,
    p: dict = None,
) -> City:
    """
    Build a city model from building footprints and point cloud data.

    Parameters
    ----------
    `city` : dtcc_model.City
        The city model to be built.
    `point_cloud` : dtcc_model.PointCloud
        The point cloud data associated with the city.
    `bounds` : dtcc_model.Bounds
        The bounds of the city domain.
    `parameters` : dict, optional
        A dictionary of parameters for the computation, by default None.

    Returns
    -------
    dtcc_model.City
        The constructed city model.

    Developer notes
    --------------
    Consider introducing a new class named Footprints
    so that a city can be built from footprints and point cloud data.
    It is somewhat strange that the input to this function is a city.
    """
    from dtcc_builder.geometry_builders.buildings import extract_roof_points,compute_building_heights
    info("Building city...")

    # Get parameters
    p = p or parameters.default()

    city = City()    
    city.add_buildings(buildings=buildings)

    # Remove outliers from point cloud
    point_cloud.remove_global_outliers(p["outlier_margin"])
 
    # Build elevation model
    terrain_raster = build_terrain_raster(
        point_cloud,
        p["elevation_model_resolution"],
        bounds,
        p["elevation_model_window_size"],
        ground_only=True,
    )
    city.add_terrain(terrain_raster)
    # city = city.simplify_buildings(p["min_building_detail"])

    # Compute building points
    buildings = extract_roof_points(
        city.buildings,
        point_cloud,
        p["statistical_outlier_remover"],
        p["roof_outlier_neighbors"],
        p["roof_outlier_margin"],
        p["ransac_outlier_remover"],
        p["ransac_outlier_margin"],
        p["ransac_iterations"],
    )

    # Compute building heights
    buildings = compute_building_heights(
        buildings,
        terrain_raster,
        p["min_building_height"], 
        p["roof_percentile"],
        overwrite=True
    )
    city.remove_buildings()
    city.add_buildings(buildings= buildings)
    return city
    

def calculate_centroid(mesh: Mesh) -> Tuple:
    """
    Calculate the centroid of the 3D bounding box from a set of vertices.

    Parameters:
    vertices (numpy.ndarray): A numpy array of shape (n, 3), where n is the number of vertices.

    Returns:
    tuple: The centroid coordinates (x, y, z) of the bounding box.
    """
    vertices = mesh.vertices
    min_coords = np.min(vertices, axis=0)
    max_coords = np.max(vertices, axis=0)
    centroid = (min_coords + max_coords) / 2
    return tuple(centroid)
    

def calculate_multisurfaces_centroid(multisurfaces: List['MultiSurface']) -> Tuple[float, float, float]:
    """
    Calculate the centroid of the 3D bounding box from a set of MultiSurfaces.

    Parameters:
    multisurfaces (List['MultiSurface'): A list of building multisurfaces.

    Returns:
    tuple: The centroid coordinates (x, y, z) of the bounding box.
    """
    vertices = []
    
    for multisurface in multisurfaces:
        for surface in multisurface.surfaces:
            vertices.extend(surface.vertices)  # Assuming surface.vertices is a list or array of vertex coordinates
    vertices = np.array(vertices)
    
    min_coords = np.min(vertices, axis=0)
    max_coords = np.max(vertices, axis=0)
    centroid = (min_coords + max_coords) / 2
    
    return tuple(centroid)
        


# ========== WORKFLOW ==========
def generate_builder_buildings(data_directory, 
                               lidar_directory, 
                               building_shapefile_path, 
                               clipping_bbox, 
                               unreal_resolution = 1009, 
                               cell_resolution = 2, 
                               translate = True, 
                               max_mesh_edge_size=5
                               ):

    # If lidar_directory does not exist or empty or if building_shapefile_path does not exist end the script
    if not Path(lidar_directory).exists() or not Path(lidar_directory).is_dir() or not Path(building_shapefile_path).exists():
        info("No lidar data or building shapefile found, skipping building generation")
        return None
    info("Generating building mesh")

    # Define bounds for processing
    bounds  = Bounds()
    bounds.xmin = clipping_bbox.bounds[0]
    bounds.ymin = clipping_bbox.bounds[1]
    bounds.xmax = clipping_bbox.bounds[2]
    bounds.ymax = clipping_bbox.bounds[3]
    info("Bounds: " + str(bounds))

    # Define parameters for processing
    p = parameters.default()
    p["outlier_margin"] = 5
    p["statistical_outlier_remover"] = False
    p["ransac_outlier_remover"] = False
    p["min_building_height"] = 4
        
    # Load building and point cloud data
    buildings_list = load_footprints(building_shapefile_path, bounds=bounds)
    pointcloud = load_pointcloud(lidar_directory, bounds=bounds)
    info(pointcloud)
    
    # Process and build city model
    city = build_city(buildings_list, pointcloud, bounds, p)

    info("Building city surface mesh...")
    
    lod1_buildings = build_lod1_buildings(city.buildings)
    city.remove_buildings()
    city.add_buildings(buildings = lod1_buildings)
  
    
    building_multisurfaces = [building.lod1 for building in lod1_buildings]
    
    mesh_centroid = calculate_multisurfaces_centroid(building_multisurfaces)

    info("Mesh centroid: " + str(mesh_centroid))

    x_translation = -bounds.xmin
    y_translation = -bounds.ymin+ ((unreal_resolution*cell_resolution)-bounds.height)
    z_translation = -mesh_centroid[2]
    
    info("Translating mesh...")
    info("x: " + str(x_translation))
    info("y: " + str(y_translation))
    info("z: " + str(z_translation))
    
    
    if translate:
        # Translate Multisurfaces
        for multisurface in building_multisurfaces:
            multisurface.translate(x = x_translation,
                         y = y_translation, 
                         z = z_translation) 
   
    # Mesh building multisurfaces.
    building_meshes = mesh_multisurfaces(multisurfaces = building_multisurfaces,max_mesh_edge_size=max_mesh_edge_size) 
    
    
    # # Generate meshes for the ground and buildings
    # surface_mesh = build_surface_mesh(
    # city,
    # min_building_detail=0.5,
    # min_building_area=10,
    # building_mesh_triangle_size=2,
    # max_mesh_size=10,
    # min_mesh_angle=25,
    # smoothing=3,
    # )

    # Merge meshes
    info("Merging meshes...")
    building_mesh = merge_meshes(building_meshes)

    file_path = Path(data_directory) / 'building_meshes.vtu'
    save_mesh(building_mesh, file_path)
    
    # Should change to fbx
    file_path = Path(data_directory) / 'building_mesh.stl'
    save_mesh(building_mesh, file_path)

    return file_path