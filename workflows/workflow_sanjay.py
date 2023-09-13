# Copyright (C) 2023 Sanjay Somanath
# Licensed under the MIT License
# This script documents the workflow for Sanjay.
# https://github.com/dtcc-platform/dtcc/issues/54

import os
import logging
from osgeo import gdal
import fiona
import geopandas as gpd
from shapely import wkt
from shapely.geometry import box
gdal.DontUseExceptions()
logging.basicConfig(level=logging.INFO)

def get_bbox_from_input(input_boundary):
    """
    Determines the bounding box of an input boundary. 

    Parameters:
    - input_boundary (str|gpd.GeoDataFrame|Polygon): The input boundary which can be one of the following:
        1. A string path to a `.shp` file or directory containing `.tif` files.
        2. A GeoDataFrame object.
        3. A Shapely Polygon object.
        4. A string in the standard WKT format.
        5. A comma-separated string like 'minx,miny,maxx,maxy' (BBOX format).
        
    Returns:
    - tuple: Bounding box in the format (minx, miny, maxx, maxy).
    
    Raises:
    - ValueError: If the input format is not recognized or invalid.
    
    Example:
    ```
    bbox = get_bbox_from_input("path/to/directory/")
    print(bbox)  # Output: (minx, miny, maxx, maxy)
    ```
    """
    # Helper message for clarity in errors
    valid_formats_message = """
    Valid input boundary formats:
    1. Shapefile path: A string path to a .shp file.
    2. Geopandas DataFrame: A GeoDataFrame object.
    3. Shapely Closed Polygon: A Shapely Polygon object.
    4. String of BBOX format: A comma-separated string like 'minx,miny,maxx,maxy'.
    5. WKT (Well-Known Text): A string in the standard WKT format.
    """

    if isinstance(input_boundary, str):
        # Check if it's a path to a file or directory
        if os.path.exists(input_boundary):
            # If it's a directory containing .tif files
            if os.path.isdir(input_boundary):
                tif_files = [f for f in os.listdir(input_boundary) if f.endswith('.tif')]
                if not tif_files:
                    raise ValueError(f"Directory {input_boundary} does not contain .tif files.")
                
                combined_bounds = None
                for tif_file in tif_files:
                    ds = gdal.Open(os.path.join(input_boundary, tif_file))
                    if ds is None:
                        continue
                    gt = ds.GetGeoTransform()
                    bounds = (gt[0], gt[3] + ds.RasterYSize * gt[5], gt[0] + ds.RasterXSize * gt[1], gt[3])
                    if combined_bounds is None:
                        combined_bounds = bounds
                    else:
                        combined_bounds = (
                            min(combined_bounds[0], bounds[0]),
                            min(combined_bounds[1], bounds[1]),
                            max(combined_bounds[2], bounds[2]),
                            max(combined_bounds[3], bounds[3])
                        )
                return combined_bounds

            # If it's a file
            with fiona.open(input_boundary) as src:
                return src.bounds

            # Check if it's WKT format
        try:
            geom = wkt.loads(input_boundary)
            return geom.bounds
        except:
            pass

        # Check if it's a BBOX format
        try:
            minx, miny, maxx, maxy = map(float, input_boundary.split(','))
            return minx, miny, maxx, maxy
        except:
            pass

        # If no valid format is found
        raise ValueError(f"Invalid input boundary string format. {valid_formats_message}")

    elif isinstance(input_boundary, gpd.GeoDataFrame):
        return input_boundary.total_bounds

    elif isinstance(input_boundary, Polygon):
        return input_boundary.bounds

    else:
        raise ValueError(f"Invalid type for input_boundary. {valid_formats_message}")


def validate_directory(dem_directory):
    """
    Validate the DEM directory to check its existence and content.

    Parameters:
    - dem_directory (str): Path to the directory.
    
    Returns:
    - list or None: List of `.tif` files in the directory or None if validation fails.
    
    Example:
    ```
    files = validate_directory("path/to/dem_directory/")
    print(files)  # Output: ['file1.tif', 'file2.tif', ...]
    ```
    """
    if not os.path.exists(dem_directory) or not os.path.isdir(dem_directory):
        logging.error(f"DEM directory not found or not a directory: {dem_directory}")
        return None

    dem_files = [file for file in os.listdir(dem_directory) if file.endswith('.tif')]
    if not dem_files:
        logging.error(f"No files found inside the DEM directory: {dem_directory}")
        return None
    return dem_files

def validate_files(filepath, expected_ext):
    """
    Validate a file's existence and its extension.

    Parameters:
    - filepath (str): Path to the file.
    - expected_ext (str): Expected extension of the file.
    
    Returns:
    - bool: True if validation passes, False otherwise.
    
    Example:
    ```
    is_valid = validate_files("path/to/file.shp", ".shp")
    print(is_valid)  # Output: True or False
    ```
    """
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return False
    elif not filepath.endswith(expected_ext):
        logging.error(f"Unexpected file type. Expected {expected_ext} but got {os.path.splitext(filepath)[1]}")
        return False
    return True

def check_attributes(filepath, required_attributes):
    """
    Check if the provided file has the necessary attributes.

    Parameters:
    - filepath (str): Path to the file.
    - required_attributes (list): List of required attributes.
    
    Returns:
    - bool: True if all attributes are present, False otherwise.
    
    Example:
    ```
    attrs = ["DETALJTYP", "ATTRIBUTE2"]
    is_valid = check_attributes("path/to/file.shp", attrs)
    print(is_valid)  # Output: True or False
    ```
    """
    with fiona.open(filepath, "r") as file:
        schema_properties = set(attr.lower() for attr in file.schema["properties"].keys())
        for attribute in required_attributes:
            if attribute.lower() not in schema_properties:
                logging.error(f"File {filepath} does not have the required {attribute} attribute")
                return False
    return True

def check_detaljtyp_values(landuse_path, landuse_mapping):
    """
    Check the 'DETALJTYP' values in a landuse file against a provided mapping.

    Parameters:
    - landuse_path (str): Path to the landuse file.
    - landuse_mapping (dict): Dictionary mapping of categories to expected values.
    
    Returns:
    - bool: True if all values match the mapping, False otherwise.
    
    Example:
    ```
    mapping = {
        "WATER": ["VATTEN"],
        "GLACIER": ["ÖPGLAC"]
    }
    is_valid = check_detaljtyp_values("path/to/landuse.shp", mapping)
    print(is_valid)  # Output: True or False
    ```
    """
    all_valid_values = [item for sublist in landuse_mapping.values() for item in sublist]
    all_valid_values_lower = set(val.lower() for val in all_valid_values)

    with fiona.open(landuse_path, "r") as landuse_file:
        for feature in landuse_file:
            detaljtyp_val = feature["properties"].get("DETALJTYP", "").lower()
            if detaljtyp_val not in all_valid_values_lower:
                logging.error(f"Invalid DETALJTYP value {detaljtyp_val} in Landuse file. Expected one of {all_valid_values}")
                return False
    return True

def validate_dem_resolution(dem_directory, expected_x_res, expected_y_res):
    """
    Validate the resolution of DEM files in a provided directory.

    Parameters:
    - dem_directory (str): Path to the directory containing DEM files.
    - expected_x_res (float): Expected X resolution.
    - expected_y_res (float): Expected Y resolution.
    
    Returns:
    - bool: True if all DEM files have the expected resolution, False otherwise.
    
    Example:
    ```
    is_valid = validate_dem_resolution("path/to/dem_directory/", 2.0, 2.0)
    print(is_valid)  # Output: True or False
    ```
    """
    # Filter for .tif files
    tif_files = [f for f in os.listdir(dem_directory) if f.lower().endswith('.tif')]

    for tif_file in tif_files:
        dem_file_path = os.path.join(dem_directory, tif_file)
        dem_dataset = gdal.Open(dem_file_path)

        if dem_dataset is None:
            logging.error(f"Failed to open DEM file: {dem_file_path}. Ensure it's a valid and accessible GeoTIFF file.")
            return False

        geo_transform = dem_dataset.GetGeoTransform()
        x_res, y_res = geo_transform[1], -geo_transform[5]

        if x_res != expected_x_res or y_res != expected_y_res:
            logging.error(f"For file {tif_file} - Expected DEM resolution of {expected_x_res}m x {expected_y_res}m, but got {x_res}m x {y_res}m")
            return False

    return True



def _validate_overlap(bboxes):
    """
    INTERNAL FUNCTION
    Check if provided bounding boxes overlap.

    Parameters:
    - bboxes (list): List of bounding boxes.
    
    Returns:
    - bool: True if all bounding boxes have overlaps, False otherwise.
    """
    def have_overlap(bbox1, bbox2):
        bbox1_bounds = bbox1.bounds
        bbox2_bounds = bbox2.bounds
        return not (bbox1_bounds[2] < bbox2_bounds[0] or
                    bbox1_bounds[0] > bbox2_bounds[2] or
                    bbox1_bounds[3] < bbox2_bounds[1] or
                    bbox1_bounds[1] > bbox2_bounds[3])

    for i in range(len(bboxes)):
        for j in range(i+1, len(bboxes)):
            if not have_overlap(bboxes[i], bboxes[j]):
                logging.error(f"No overlap found between bounding boxes {i} and {j}.")
                return False
    return True


def validate_input_data(dem_directory, landuse_path, road_path, optional_clipping_boundary=None, expected_x_res=2.0, expected_y_res=2.0):
    """
    Comprehensive validation function that combines multiple validation steps.

    Parameters:
    - dem_directory (str): Path to the DEM directory.
    - landuse_path (str): Path to the landuse shapefile.
    - road_path (str): Path to the road shapefile.
    - optional_clipping_boundary (str, optional): Path to an optional clipping boundary. Defaults to None.
    - expected_x_res (float, optional): Expected X resolution. Defaults to 2.0m.
    - expected_y_res (float, optional): Expected Y resolution. Defaults to 2.0m.
    
    Returns:
    - None: Just logs messages.
    
    Example:
    ```
    validate_input_data("path/to/dem_directory/", "path/to/landuse.shp", "path/to/road.shp")
    ```
    """
    if not validate_directory(dem_directory):
        return

    if not validate_files(landuse_path, '.shp') or not validate_files(road_path, '.shp'):
        return

    required_attributes = ["DETALJTYP"]
    if not check_attributes(landuse_path, required_attributes) or not check_attributes(road_path, required_attributes):
        return

    if not check_detaljtyp_values(landuse_path, landuse_mapping):
        return

    if not validate_dem_resolution(dem_directory, expected_x_res, expected_y_res):
        return

    dem_bbox = box(*get_bbox_from_input(dem_directory))
    landuse_bbox = box(*get_bbox_from_input(landuse_path))
    road_bbox = box(*get_bbox_from_input(road_path))
    
    bboxes_to_check = [dem_bbox, landuse_bbox, road_bbox]
    if optional_clipping_boundary:
        bboxes_to_check.append(box(*get_bbox_from_input(optional_clipping_boundary)))
        
    if not _validate_overlap(bboxes_to_check):
        return

    logging.info("Validation successful!")

landuse_mapping = {
    "WATER": ["VATTEN"],
    "GLACIER": ["ÖPGLAC"],
    "BUILDINGS": ["BEBSLUT", "BEBHÖG", "BEBLÅG", "BEBIND"],
    "FARMING": ["ODLÅKER", "ODLFRUKT"],
    "OPEN AREAS": ["ÖPMARK", "ÖPKFJÄLL", "ÖPTORG"],
    "FOREST": ["SKOGBARR", "SKOGLÖV", "SKOGFBJ"],
    "UNMAPPED": ["MRKO"]
}
