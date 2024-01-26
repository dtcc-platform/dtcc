# Copyright (C) 2023 Sanjay Somanath
# Licensed under the MIT License
# This script documents the workflow for Sanjay.
# https://github.com/dtcc-platform/dtcc/issues/54
# Refactored to work with pip by Daniel Soljie

# Standard library imports

import numpy as np
from dtcc_builder.meshing import merge_meshes
import logging
from pathlib import Path
from dtcc import (
    Bounds,
    parameters,
    load_city,
    load_pointcloud,
    build_city,
    build_building_meshes,
    build_terrain_mesh,
    build_city_surface_mesh,
    save_mesh
    )
# ========== INTERNAL CONFIGURATION ==========
# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Unreal_Building_Generator')

# ========== WORKFLOW ==========
def generate_builder_buildings( data_directory, lidar_directory, building_shapefile_path, clipping_bbox, unreal_resolution = 1009, cell_resolution = 2):

    # If lidar_directory does not exist or empty or if building_shapefile_path does not exist end the script
    if not Path(lidar_directory).exists() or not Path(lidar_directory).is_dir() or not Path(building_shapefile_path).exists():
        logger.info("No lidar data or building shapefile found, skipping building generation")
        return None
    logger.info("Generating building mesh")

    # Define bounds for processing
    bounds  = Bounds()
    bounds.xmin = clipping_bbox.bounds[0]
    bounds.ymin = clipping_bbox.bounds[1]
    bounds.xmax = clipping_bbox.bounds[2]
    bounds.ymax = clipping_bbox.bounds[3]
    logger.info("Bounds: " + str(bounds))

    # Define parameters for processing
    p = parameters.default()
    p["outlier_margin"] = 5
    p["statistical_outlier_remover"] = False
    p["ransac_outlier_remover"] = False
    p["min_building_height"] = 4
    
    def calculate_centroid(mesh):
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
    # Load building and point cloud data
    city = load_city(building_shapefile_path, bounds=bounds)
    pointcloud = load_pointcloud(lidar_directory, bounds=bounds)

    # Process and build city model
    city = build_city(city, pointcloud, bounds, p)

    logger.info("Building city surface mesh...")

    # Generate meshes for the ground and buildings
    building_meshes = build_building_meshes(city, p)


    # Merge meshes
    logger.info("Merging meshes...")
    building_mesh = merge_meshes(building_meshes)

    mesh_centroid = calculate_centroid(building_mesh)

    logger.info("Mesh centroid: " + str(mesh_centroid))

    z_translation = -mesh_centroid[2]
    
    logger.info("Translating mesh...")
    logger.info("x: " + str(-bounds.xmin))
    logger.info("y: " + str(-bounds.ymin+ ((unreal_resolution*cell_resolution)-bounds.height)))
    logger.info("z: " + str(z_translation))


    building_mesh.translate(-bounds.xmin,-bounds.ymin+ ((unreal_resolution*cell_resolution)-bounds.height),z_translation)
    # Should change to fbx
    file_path = Path(data_directory) / 'building_mesh.stl'
    save_mesh(building_mesh, file_path)

    return file_path