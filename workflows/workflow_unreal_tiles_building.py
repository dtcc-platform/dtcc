import numpy as np
from dtcc_builder.meshing import merge_meshes
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


def generate_builder_buildings( data_directory, lidar_directory, building_shapefile_path, clipping_bbox, unreal_resolution = 1009, cell_resolution = 2):

    bounds  = Bounds()
    bounds.xmin = clipping_bbox[0]
    bounds.ymin = clipping_bbox[1]
    bounds.xmax = clipping_bbox[2]
    bounds.ymax = clipping_bbox[3]

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
    city = load_city(buildings_path, bounds=bounds)
    pointcloud = load_pointcloud(pointcloud_path, bounds=bounds)

    # Process and build city model
    city = build_city(city, pointcloud, bounds, p)

    # Generate meshes for the ground and buildings
    building_meshes = build_building_meshes(city, p)

    # Merge meshes
    building_mesh = merge_meshes(building_meshes)

    mesh_centroid = calculate_centroid(building_mesh)

    z_translation = -mesh_centroid[2]

    building_mesh.translate(-bounds.xmin,-bounds.ymin+ ((unreal_resolution*cell_resolution)-bounds.height),z_translation)

    save_mesh(building_mesh, data_directory / 'building_mesh.fbx')

    return data_directory / 'building_mesh.fbx'