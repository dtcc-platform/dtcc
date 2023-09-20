# Copyright (C) 2023 Sanjay Somanath
# Licensed under the MIT License
# This script documents the workflow for Sanjay.
# https://github.com/dtcc-platform/dtcc/issues/54

# Standard library imports
import logging
import os
import shutil
import json
import zipfile
import tempfile
import re

# Third-party imports
import fiona
import geopandas as gpd
from matplotlib.patches import Rectangle, Patch
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal, osr
import rasterio
from rasterio.features import geometry_mask, rasterize
from rasterio.mask import mask
from rasterio.transform import from_origin
from scipy.signal import convolve2d
from shapely import wkt
from shapely.geometry import box
from shapely.geometry.polygon import Polygon
gdal.SetConfigOption('CPL_LOG_ERRORS', 'OFF')


# ========== INTERNAL CONFIGURATION ==========
gdal.DontUseExceptions()
logging.basicConfig(level=logging.INFO)

# ========== CONSTANTS ==========

# Spatial constants


CELL_RESOLUTION = 2                         # TODO This is the resolution of data we get from LM, 2m per pixel
# https://docs.unrealengine.com/4.27/en-US/BuildingWorlds/Landscape/TechnicalGuide/
VALID_UE_RESOLUTIONS = sorted([1009,
                               8129,
                               4033,
                               2017,
                               5055,
                               253,
                               127])

BLUR_KERNEL = np.array([
    [1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1],
    [1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1],
    [1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1],
    [1,  1,  1,  1,  4,  6,  4,  1,  1,  1,  1],
    [1,  1,  1,  4, 16, 24, 16,  4,  1,  1,  1],
    [1,  1,  1,  6, 24, 36, 24,  6,  1,  1,  1],
    [1,  1,  1,  4, 16, 24, 16,  4,  1,  1,  1],
    [1,  1,  1,  1,  4,  6,  4,  1,  1,  1,  1],
    [1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1],
    [1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1],
    [1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1]
])

# ========== DATA MAPPING CONFIGURATION ==========

# Buffer values for specific keys           # TODO requires a review of LM classes
BUFFER_DICT = {
    "VÄGBN.M": 10,
    "VÄGGG.D": 10,
    "VÄGGG.M": 10,
    "VÄGKV.M": 10,
    "VÄGBNU.M": 10
}

# Landuse classification mapping
LANDUSE_MAPPING = {                         # TODO Should the user decide this?
    "WATER": ["VATTEN"],                    # Consolidating "VATTEN" values under WATER
    "GLACIER": ["ÖPGLAC"],
    "BUILDINGS": ["BEBSLUT", "BEBHÖG", "BEBLÅG", "BEBIND"],
    "FARMING": ["ODLÅKER", "ODLFRUKT"],
    "OPEN AREAS": ["ÖPMARK", "ÖPKFJÄLL", "ÖPTORG"],
    "FOREST": ["SKOGBARR", "SKOGLÖV", "SKOGFBJ"],
    "UNMAPPED": ["MRKO"]                    # Unused as of now
}

def check_and_clear_data():
    path = 'data/unreal_tiles'
    
    if os.path.exists(path):
        logging.warning(f"Data is already present at {path}. It will be cleared.")
        
        try:
            shutil.rmtree(path)
            logging.info(f"Data cleared from {path}.")
        except Exception as e:
            logging.error(f"An error occurred while trying to clear data from {path}. Error: {e}")

    else:
        logging.info(f"No data found at {path}.")

# To test the function, simply call it:
# check_and_clear_data()

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
                logging.error(
                    f"Invalid DETALJTYP value {detaljtyp_val} in Landuse file. Expected one of {all_valid_values}")
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
            logging.error(
                f"For file {tif_file} - Expected DEM resolution of {expected_x_res}m x {expected_y_res}m, but got {x_res}m x {y_res}m")
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
        for j in range(i + 1, len(bboxes)):
            if not have_overlap(bboxes[i], bboxes[j]):
                logging.error(f"No overlap found between bounding boxes {i} and {j}.")
                return False
    return True

def get_intersection_percentage(bounding_box, other_boxes):
    """
    Compute the intersection percentage between a bounding box and a list of other bounding boxes.
    """
    intersection_area = sum([bounding_box.intersection(b).area for b in other_boxes])
    total_area = sum([b.area for b in other_boxes])
    
    return (intersection_area / total_area) * 100

def validate_input_data(dem_directory, landuse_path, road_path, optional_clipping_boundary=None, expected_x_res=2.0,
                        expected_y_res=2.0):
    """
    Comprehensive validation function that combines multiple validation steps.
    """

    if not validate_directory(dem_directory):
        return
    logging.info("Directory validation successful.")

    if not validate_files(landuse_path, '.shp') or not validate_files(road_path, '.shp'):
        return
    logging.info("File validation successful.")

    required_attributes = ["DETALJTYP"]
    if not check_attributes(landuse_path, required_attributes) or not check_attributes(road_path, required_attributes):
        return
    logging.info("Attribute validation successful.")

    if not check_detaljtyp_values(landuse_path, LANDUSE_MAPPING):
        return
    logging.info("Detaljtyp values validation successful.")

    if not validate_dem_resolution(dem_directory, expected_x_res, expected_y_res):
        logging.info("DEM resolution validation failed.")
        return
    logging.info("DEM resolution validation successful.")

    dem_bbox = box(*get_bbox_from_input(dem_directory))
    landuse_bbox = box(*get_bbox_from_input(landuse_path))
    road_bbox = box(*get_bbox_from_input(road_path))

    bboxes_to_check = [dem_bbox, landuse_bbox, road_bbox]

    clipping_bbox = None
    if optional_clipping_boundary:
        optional_bbox = box(*get_bbox_from_input(optional_clipping_boundary))
        coverage_percentage = get_intersection_percentage(optional_bbox, bboxes_to_check)
        logging.info(f"Optional bounding box covers {coverage_percentage:.2f}% of the total intersection.")
        clipping_bbox =  optional_bbox
    else:
        intersection_bbox = bboxes_to_check[0]
        for bbox in bboxes_to_check[1:]:
            intersection_bbox = intersection_bbox.intersection(bbox)
        clipping_bbox = intersection_bbox
    
    bboxes_to_check.append(clipping_bbox)
    if not _validate_overlap(bboxes_to_check):
        logging.info("Overlap validation failed.")
        return
    logging.info("Overlap validation successful.")
    
    
    logging.info("Validation successful! Please close the map to continue...")
    
    
    landuse_crs = gpd.read_file(landuse_path).crs
    plot_bboxes(dem_bbox, landuse_bbox, road_bbox, clipping_bbox,crs = landuse_crs)
    
    return clipping_bbox



def plot_bboxes(dem_bbox, landuse_bbox, road_bbox, optional_bbox, crs):    
    # Create a single GeoDataFrame with all the bounding boxes
    data = {
        'geometry': [dem_bbox, landuse_bbox, road_bbox, optional_bbox],
        'label': ['DEM', 'Landuse', 'Roads', 'Clipping boundary'],
        'color': ['red', 'green', 'blue', 'yellow'],
        'hatch': ['/', '\\', '|', '-']
    }
    gdf = gpd.GeoDataFrame(data, crs=crs)
    
    # Plot using gdf.plot()
    fig, ax = plt.subplots(figsize=(6, 6))
    for _, row in gdf.iterrows():
        gdf[gdf['label'] == row['label']].plot(ax=ax, color=row['color'], edgecolor=row['color'], hatch=row['hatch'], alpha=0.2)
    
    # For the legend:
    handles = [Patch(facecolor=row['color'], edgecolor='black', hatch=row['hatch'], label=row['label'], alpha=0.5) for _, row in gdf.iterrows()]
    ax.legend(handles=handles, loc="upper left")
    ax.set_title("Bounding boxes. Please close this window to continue.")
    
    plt.show(block=True)



# PROCESSING DEM DATA
def merge_dem_tiles(dem_directory, output_directory):
    """
    Merge multiple DEM tiles from a directory into a single mosaic using GDAL.
    
    Parameters:
        dem_directory (str): Directory containing the DEM tiles.
        output_directory (str) : Directory where the merged DEM will be saved.
        
    Returns:
        str: Path to the merged DEM.
    """
    output_path = os.path.join(output_directory, 'merged_dem.tif')
    tile_list = [os.path.join(dem_directory, file) for file in os.listdir(dem_directory) if file.endswith('.tif')]

    gdal.Warp(output_path, tile_list)

    return output_path


def clip_raster_with_boundary(dem_path, clipping_boundary_Polygon):
    """
    Clip the DEM raster using a provided boundary WKT.
    
    Parameters:
        dem_path (str): Path to the DEM geotiff file.
        clipping_boundary_wkt (str): The WKT string representation of a geometry.
        
    Returns:
        numpy.ndarray: Clipped DEM data.
        rasterio.transform.Affine: Transformation matrix for the clipped data.
    """
    # Convert the WKT string into a shapely geometry
    geom = clipping_boundary_Polygon
    # Convert the geometry into GeoJSON format
    geoms = [geom.__geo_interface__]
    
    with rasterio.open(dem_path) as src:
        out_image, out_transform = mask(src, geoms, crop=True)
        out_meta = src.meta

    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    
    output_path = dem_path.replace('.tif', '_clipped.tif')
    
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(out_image)

    return output_path


def divide_raster_into_tiles(dem_path, cell_resolution):
    """
    Divide the DEM raster into tiles based on the provided cell resolution.
    
    Parameters:
        dem_path (str): Path to the DEM geotiff file.
        cell_resolution (int): Desired resolution of each cell (tile size).
    """
    ds = gdal.Open(dem_path)
    if ds is None:
        raise ValueError(
            f"Cannot open raster file {dem_path}. Please check if the file exists and is a valid raster format.")

    width, height = ds.RasterXSize, ds.RasterYSize

    tile_row = 0
    for y in range(0, height, cell_resolution):
        tile_col = 0
        for x in range(0, width, cell_resolution):
            output_path = os.path.join(os.path.dirname(dem_path), f'Tile_X{tile_col}_Y{tile_row}.png')
            gdal.Translate(
                output_path,
                dem_path,
                srcWin=[x, y, cell_resolution, cell_resolution],
                format="PNG"
            )
            tile_col += 1
        tile_row += 1

    ds = None  # Close dataset


def divide_gdal_raster_into_tiles(ds, cell_resolution, output_directory):
    """
    Divide the provided GDAL raster dataset into tiles based on the provided cell resolution.
    
    Parameters:
        ds (gdal.Dataset): Input GDAL raster dataset.
        cell_resolution (int): Desired resolution of each cell (tile size).
        output_directory (str): Directory where the tiles will be saved.
    """
    if ds is None:
        raise ValueError("Provided GDAL raster dataset is None.")

    width, height = ds.RasterXSize, ds.RasterYSize

    # Determine the minimum and maximum values of the raster
    band = ds.GetRasterBand(1)
    min_val, max_val = band.ComputeRasterMinMax()

    # Define the target min and max based on Unreal's range
    target_min, target_max = 0, 255

    # Now loop over the raster to divide it into tiles and rescale the values
    tile_row = 0
    for y in range(0, height, cell_resolution):
        tile_col = 0
        for x in range(0, width, cell_resolution):
            output_path = os.path.join(output_directory, f'Tile_X{tile_col}_Y{tile_row}.png')
            gdal.Translate(
                output_path,
                ds,
                srcWin=[x, y, cell_resolution, cell_resolution],
                format="PNG",
                scaleParams=[[min_val, max_val, target_min, target_max]]  # Rescale values
            )
            tile_col += 1
        tile_row += 1



def calculate_z_scale(dem_path):
    """
    Calculate the Z scale for Unreal Engine based on the DEM data.
    
    Parameters:
        dem_path (str): Path to the DEM geotiff file.
        
    Returns:
        float: Calculated Z scale.
    """
    ds = gdal.Open(dem_path)
    if ds is None:
        raise ValueError(f"Unable to open the DEM file at {dem_path}")

    band = ds.GetRasterBand(1)
    min_value, max_value = band.ComputeRasterMinMax()

    # Taking the highest absolute elevation difference (in case of depressions)
    max_abs_difference = max(abs(min_value), abs(max_value))

    # Conversion to centimeters
    max_height_cm = max_abs_difference * 100
    z_scale = max_height_cm * 0.001953125

    # Cleanup
    ds = None

    return z_scale



def resample_dem(dem_path, target_resolution=CELL_RESOLUTION):
    """
    Resample DEM to the target resolution using GDAL.
    
    Parameters:
        dem_path (str): Path to the DEM geotiff file.
        target_resolution (float): The desired resolution in ground units (e.g., 1 for 1m).
        
    Returns:
        str: Path to the resampled DEM.
    """
    output_path = dem_path.replace('.tif', '_resampled.tif')

    # Open the DEM raster
    ds = gdal.Open(dem_path)
    if not ds:
        raise ValueError(f"Failed to open dataset at {dem_path}")

    # Resample using the Warp function
    out_ds = gdal.Warp(output_path,
                       ds,
                       xRes=target_resolution,
                       yRes=target_resolution,
                       resampleAlg='bilinear')

    # Check the result
    if not out_ds:
        raise ValueError(f"Resampling failed for dataset at {dem_path}")

    # Close the datasets to free up resources
    ds = None
    out_ds = None

    return output_path


def generate_heightmap(dem_path, clipping_boundary=None, output_folder="data", ue_cell_resolution=1009):
    # Ensure the specified Unreal resolution is valid
    if ue_cell_resolution not in VALID_UE_RESOLUTIONS:
        raise ValueError(
            f"Invalid UE cell resolution: {ue_cell_resolution}. Valid resolutions are {VALID_UE_RESOLUTIONS}.")

    # Create the output directories if they don't exist
    unreal_tiles_dir = os.path.join(output_folder, "unreal_tiles")
    dem_output_dir = os.path.join(output_folder, "unreal_tiles/DEM")

    for directory in [output_folder, unreal_tiles_dir, dem_output_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # If dem_path is a directory, merge tiles
    if os.path.isdir(dem_path):
        dem_path = merge_dem_tiles(dem_path, dem_output_dir)

    # Resample the merged DEM
    dem_path = resample_dem(dem_path)

    # Clip the raster using the specified boundary, if provided
    if clipping_boundary:
        dem_path = clip_raster_with_boundary(dem_path, clipping_boundary)

    # Calculate the Z scale for the DEM data
    z_scale = calculate_z_scale(dem_path)

    # Move the processed DEM to DEM output directory and update dem_path to point to its new location
    new_dem_path = os.path.join(dem_output_dir, os.path.basename(dem_path))
    shutil.move(dem_path, new_dem_path)
    dem_path = new_dem_path

    # Divide the raster into tiles of the specified resolution and save in unreal_tiles directory
    divide_raster_into_tiles(dem_path, ue_cell_resolution)

    # delete merge_dem.tif and merged_dem_resampled.tif from dem_output_dir
    os.remove(os.path.join(dem_output_dir, "merged_dem.tif"))
    os.remove(os.path.join(dem_output_dir, "merged_dem_resampled.tif"))

    # Return the Z scale value
    return z_scale


# PROCESSING LANDUSE DATA AND ROAD DATA
def rasterize_landuse(subtracted, cell_resolution, output_dir, category):
    """
    Rasterize the subtracted land use data.
    """
    # raster_path = os.path.join(output_dir, category, f"temp_{category}_mask.tif")

    bounds = subtracted.total_bounds
    dx = dy = cell_resolution
    width = int((bounds[2] - bounds[0]) / dx)
    height = int((bounds[3] - bounds[1]) / dy)
    # Create the transform
    transform = from_origin(bounds[0], bounds[3], dx, dy)

    # Rasterize the shapes into an array
    raster = rasterize(
        ((geom, 1) for geom in subtracted.geometry),
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=rasterio.uint8
    )
    return raster, transform

# TODO Hardcoded crs
def create_gdal_raster_from_array(array, transform, output_path=None, epsg=3006, nodata=None):
    """
    Create a GDAL raster dataset from a numpy array.
    
    Parameters:
        array (numpy.ndarray): The array to be converted to a raster.
        transform (affine.Affine): The affine transformation for the raster.
        output_path (str, optional): The path where the raster should be saved. If None, creates an in-memory raster.
        epsg (int, optional): The EPSG code for the raster's projection. Defaults to 4326 (WGS84).
        nodata (int or float, optional): The NoData value for the raster. If None, no NoData value is set.
    
    Returns:
        osgeo.gdal.Dataset: The GDAL raster dataset.
    """

    # Determine the driver based on whether an output_path is provided
    driver_name = 'GTiff' if output_path else 'MEM'
    driver = gdal.GetDriverByName(driver_name)
    raster_ds = driver.Create(output_path if output_path else '', array.shape[1], array.shape[0], 1, gdal.GDT_Byte)

    # Apply the transform to the raster dataset
    raster_ds.SetGeoTransform(transform.to_gdal())

    # Set projection based on the provided EPSG code
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    raster_ds.SetProjection(srs.ExportToWkt())

    # Write the numpy array to the dataset
    raster_band = raster_ds.GetRasterBand(1)
    raster_band.WriteArray(array)

    # Set the NoData value if provided
    if nodata is not None:
        raster_band.SetNoDataValue(nodata)

    # Properly close the dataset's band
    raster_band = None

    return raster_ds


def blur_raster_array(raster_array, transform):
    """
    Blur the rasterized land use data provided as a numpy array.
    """
    # Create a 3x3 averaging filter
    kernel = BLUR_KERNEL
    """kernel = np.array([
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]
    ]) / 9  # Dividing by 9 to make the sum of all elements equal to 1
    """
    # Convolve the image with the kernel
    blurred = convolve2d(raster_array, kernel, mode='same', boundary='symm')
    # blurred = ndimage.gaussian_filter(raster_array, sigma=2)

    blurred_gdal_object = create_gdal_raster_from_array(blurred, transform)
    return blurred_gdal_object


def generate_land_use_mask(landuse_vector_path,
                           road_vector_path,
                           optional_clipping_boundary=None,
                           landuse_mapping=LANDUSE_MAPPING,
                           road_buffer_dict=BUFFER_DICT,
                           cell_resolution=CELL_RESOLUTION,
                           ue_cell_resolution=1009,
                           output_dir="data/unreal_tiles"):
    landuse = gpd.read_file(landuse_vector_path)
    roads = gpd.read_file(road_vector_path)

    # Clip the landuse and road data using the optional clipping boundary, if provided

    if optional_clipping_boundary:
        clipping_gdf = gpd.GeoDataFrame({'geometry': [optional_clipping_boundary]})
        clipping_gdf.set_crs(landuse.crs, inplace=True)
        landuse = gpd.clip(landuse, clipping_gdf)
        roads = gpd.clip(roads, clipping_gdf)

    # Buffer roads
    roads['geometry'] = roads.apply(lambda row: row['geometry'].buffer(road_buffer_dict.get(row['DETALJTYP'], 0)),
                                    axis=1)
    buffered_roads = roads.dissolve()

    # Write roads first
    category_dir = os.path.join(output_dir, 'ROAD')
    os.makedirs(category_dir, exist_ok=True)
    raster, transform = rasterize_landuse(buffered_roads, cell_resolution, output_dir, 'ROAD')
    blurred_raster = blur_raster_array(raster, transform)

    # Tile the blurred raster
    divide_gdal_raster_into_tiles(blurred_raster, ue_cell_resolution, category_dir)

    for category, details in landuse_mapping.items():
        combined_features = landuse[landuse['DETALJTYP'].isin(details)]

        if combined_features.empty:
            logging.info(f"No features found for category {category}. Skipping...")
            continue

        # Subtract buffered road network
        subtracted = gpd.overlay(combined_features, buffered_roads, how="difference")
        # Set the bbox for the subtracted data as the clipping boundary
        subtracted = gpd.clip(subtracted, optional_clipping_boundary)

        # Plot the GeoDataFrame
        fig, ax = plt.subplots(figsize=(6, 6))

        # Plot the 'subtracted' GeoDataFrame
        subtracted.plot(ax=ax, color='lightgray', label='Subtracted Data')

        # Plot the 'optional_clipping_boundary' polygon with a different color
        gpd.GeoSeries([optional_clipping_boundary], crs=subtracted.crs).plot(ax=ax, color='none', edgecolor='blue', label='Clipping Boundary')

        # Create proxy artists for legend
        subtracted_patch = mpatches.Patch(color='lightgray', label='Subtracted Data')
        boundary_patch = mpatches.Patch(edgecolor='blue', facecolor='none', label='Clipping Boundary')

        # Set title, labels, and legend
        
        ax.set_title(f"Category: {category}. Please close this window to continue.")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.legend(handles=[subtracted_patch, boundary_patch])

        plt.show(block=True)


        logging.info(f"Processing category {category} with {len(subtracted)} features.")

        # Rasterize the subtracted data
        category_dir = os.path.join(output_dir, category)
        os.makedirs(category_dir, exist_ok=True)

        raster, transform = rasterize_landuse(subtracted, cell_resolution, output_dir, category)
        blurred_raster = blur_raster_array(raster, transform)

        # Tile the blurred raster
        divide_gdal_raster_into_tiles(blurred_raster, ue_cell_resolution, category_dir)

def write_metadata(z_scale, expected_x_res=2.0, expected_y_res=2.0, output_folder="data/unreal_tiles/"):
    """
    Writes a metadata file with the given resolutions and output folder.

    Args:
    - expected_x_res (float): Expected resolution for x.
    - expected_y_res (float): Expected resolution for y.
    - output_folder (str): Directory to write the metadata file.
    - z_scale (float): Scale for z. Needs to be provided if used.

    Returns:
    - None
    """

    x_scale = expected_x_res * 100
    y_scale = expected_y_res * 100

    metadata = {
        "x_scale": x_scale,
        "y_scale": y_scale,
        "z_scale": z_scale
    }
    logging.info("Metadata generated successfully!")
    with open(os.path.join(output_folder, "metadata.json"), "w") as f:
        json.dump(metadata, f)

def generate_overlay_data(overlay_data_directory, clipping_boundary):

    logging.info("Generating overlay data...")

    # Check if overlay_data_directory exists
    if not os.path.exists(overlay_data_directory):
        logging.warning(f"Directory {overlay_data_directory} not found. Continuing without generating overlay data...")
        return

    # Check if overlay_data_directory is not empty
    if not os.listdir(overlay_data_directory):
        logging.error("Overlay data directory is empty.")
        return

    # Check if clipping_boundary is a Shapely Polygon
    if not isinstance(clipping_boundary, Polygon):
        logging.error("Invalid clipping boundary provided. It should be a Shapely Polygon.")
        return

    all_gdfs = []
    zip_file_names = []

    pattern = r'(\d+)_dBA'
    regex_found = False

    for filename in os.listdir(overlay_data_directory):
        if filename.endswith('.zip'):
            zip_file_names.append(filename)

            match = re.search(pattern, filename)
            if match:
                db_value = match.group(1)
                regex_found = True
            else:
                db_value = 'unknown'

            with tempfile.TemporaryDirectory() as tempdir:
                with zipfile.ZipFile(os.path.join(overlay_data_directory, filename), 'r') as zip_ref:
                    zip_ref.extractall(tempdir)

                for root, _, files in os.walk(tempdir):                
                    for file in files:
                        if file.endswith('.shp'):
                            gdf = gpd.read_file(os.path.join(root, file))
                            #set crs
                            gdf.to_crs(epsg=3006, inplace=True)
                            gdf['db'] = db_value
                            all_gdfs.append(gdf)
                            break

    if not regex_found:
        logging.error("Regex pattern not found in the directory filenames.")
        return

    merged_gdf = gpd.pd.concat(all_gdfs, ignore_index=True)

    fig, ax = plt.subplots(figsize=(6, 6))
    merged_gdf.plot(column='db', ax=ax, cmap='gray')


    #if not merged_gdf.geometry.intersects(clipping_boundary).any():
    #    logging.error("Clipping boundary does not intersect with the GeoDataFrame. Exiting...")
    #    return

    merged_gdf = merged_gdf[merged_gdf.geometry.within(clipping_boundary)]
    logging.info(f"Number of loaded shapefiles: {len(all_gdfs)}")
    #TODO BBOX is returning nan
    bbox = merged_gdf.total_bounds
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    aspect_ratio = width / height

    fig_height = 20
    fig_width = fig_height * aspect_ratio
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    merged_gdf.plot(column='db', ax=ax, cmap='gray')

    ax.axis('off')
    ax.set_facecolor('black')
    fig.set_facecolor('black')

    output_directory = os.path.join('data', 'unreal_tiles', 'OVERLAY')
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_path = os.path.join(output_directory, 'output_plot.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0, facecolor=fig.get_facecolor())
    plt.show(block=True)
    plt.close()

    logging.info(f"Plot saved to {output_path}")

def generate_unreal_tiles(dem_directory, landuse_path, road_path):
    """
    Process and validate input data, generate heightmap and land use mask, 
    and then write metadata.

    Args:
    - dem_directory (str): Directory for DEM.
    - landuse_path (str): Path for land use.
    - road_path (str): Path for roads.

    Returns:
    - None
    """
    # Check if data directory exists
    check_and_clear_data()
    
    logging.info("Generating Unreal tiles...")
    # Validate input data
    clipping_bbox = validate_input_data(dem_directory, landuse_path, road_path)
    
    # Generate heightmap
    z_scale = generate_heightmap(dem_directory, clipping_boundary=clipping_bbox)
    
    # Generate land use mask
    generate_land_use_mask(landuse_path, road_path, optional_clipping_boundary=clipping_bbox)

    # Generate overlay data
    overlay_data_directory = "data\\overlay_data"
    generate_overlay_data(overlay_data_directory, clipping_bbox)
    
    # Write metadata
    write_metadata(z_scale)
    

if __name__ == "__main__":
    # Define input paths
    DEM_DIRECTORY = "data\\dem_data"
    LANDUSE_PATH = "data\\landuse_data\\my_south.shp"
    ROAD_PATH = "data\\road_data\\vl_riks.shp"

    # Call the function
    generate_unreal_tiles(DEM_DIRECTORY, LANDUSE_PATH, ROAD_PATH)