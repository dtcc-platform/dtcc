# Copyright (C) 2023 Sanjay Somanath
# Licensed under the MIT License
# This script documents the workflow for Sanjay.
# https://github.com/dtcc-platform/dtcc/issues/54
# Refactored to work with pip by Daniel Soljie

# Standard library imports
import argparse
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
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

import numpy as np
import rasterio
from rasterio.features import geometry_mask, rasterize
from rasterio.mask import mask
from rasterio.transform import from_origin
from rasterio.crs import CRS
from rasterio.merge import merge
from rasterio.enums import Resampling
from rasterio.io import DatasetReader, MemoryFile

from scipy.signal import convolve2d
from shapely import wkt
from shapely.geometry import box
from shapely.geometry.polygon import Polygon

# DTCC imports 

from dtcc import Bounds
from workflow_unreal_tiles_building import generate_builder_buildings

# ========== INTERNAL CONFIGURATION ==========
# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Unreal_Tile_Generator')

# ========== CONSTANTS ==========

# Define the path to your JSON configuration file
config_file_path = 'unreal_tiles_config.json'
SUPPRESS_PLOTS = None
UE_CELL_RESOLUTION = 1009
# Read the JSON file and extract the variables
with open(config_file_path, 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

    # Constants
    DEFAULT_EPSG = config['constants']['DEFAULT_EPSG']
    CELL_RESOLUTION = config['constants']['CELL_RESOLUTION']
    VALID_UE_RESOLUTIONS = config['constants']['VALID_UE_RESOLUTIONS']
    # Convert BLUR_KERNEL to a NumPy array
    BLUR_KERNEL = np.array(config['constants']['BLUR_KERNEL'])
    
    # Data Mapping Configuration
    ROAD_CATEGORY_VARIABLE = config['data_mapping_configuration']['ROAD_CATEGORY_VARIABLE']
    BUFFER_DICT = config['data_mapping_configuration']['BUFFER_DICT']
    DEFAULT_ROAD_BUFFER = config['data_mapping_configuration']['DEFAULT_ROAD_BUFFER']
    LANDUSE_CATEGORY_VARIABLE = config['data_mapping_configuration']['LANDUSE_CATEGORY_VARIABLE']
    LANDUSE_MAPPING = config['data_mapping_configuration']['LANDUSE_MAPPING']

class DataUtils:
    def check_and_clear_data():
        path = 'data/unreal_tiles'
        
        if os.path.exists(path):
            logger.warning(f"Data is already present at {path}. It will be cleared.")
            
            try:
                shutil.rmtree(path)
                logger.info(f"Data cleared from {path}.")
            except Exception as e:
                logger.error(f"An error occurred while trying to clear data from {path}. Error: {e}")

        else:
            logger.info(f"No data found at {path}.")

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
                        with rasterio.open(os.path.join(input_boundary, tif_file)) as src:
                            # Get bounds from src
                            bounds = src.bounds
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
            logger.error(f"DEM directory not found or not a directory: {dem_directory}")
            return None

        dem_files = [file for file in os.listdir(dem_directory) if file.endswith('.tif')]
        if not dem_files:
            logger.error(f"No files found inside the DEM directory: {dem_directory}")
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
            logger.error(f"File not found: {filepath}")
            return False
        elif not filepath.endswith(expected_ext):
            logger.error(f"Unexpected file type. Expected {expected_ext} but got {os.path.splitext(filepath)[1]}")
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
                    logger.error(f"File {filepath} does not have the required {attribute} attribute")
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
                detaljtyp_val = feature["properties"].get(LANDUSE_CATEGORY_VARIABLE, "").lower()
                if detaljtyp_val not in all_valid_values_lower:
                    logger.error(
                        f"Invalid category value {detaljtyp_val} in Landuse file. Expected one of {all_valid_values}")
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
            
            try:
                with rasterio.open(dem_file_path) as dem_dataset:
                    x_res, y_res = dem_dataset.res
                    
                    if x_res != expected_x_res or y_res != expected_y_res:
                        logger.error(
                            f"For file {tif_file} - Expected DEM resolution of {expected_x_res}m x {expected_y_res}m, but got {x_res}m x {y_res}m")
                        return False
            except rasterio.errors.RasterioIOError:
                logger.error(f"Failed to open DEM file: {dem_file_path}. Ensure it's a valid and accessible GeoTIFF file.")
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
                    logger.error(f"No overlap found between bounding boxes {i} and {j}.")
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

        if not DataUtils.validate_directory(dem_directory):
            return
        logger.info("Directory validation successful.")

        if not DataUtils.validate_files(landuse_path, '.shp') or not DataUtils.validate_files(road_path, '.shp'):
            return
        logger.info("File validation successful.")

        required_attributes_road = [ROAD_CATEGORY_VARIABLE]
        required_attribute_landuse = [LANDUSE_CATEGORY_VARIABLE]
        if not DataUtils.check_attributes(landuse_path, required_attribute_landuse) or not DataUtils.check_attributes(road_path, required_attributes_road):
            return
        logger.info("Attribute validation successful.")

        if not DataUtils.check_detaljtyp_values(landuse_path, LANDUSE_MAPPING):
            return
        logger.info("Categories values validation successful.")

        if not DataUtils.validate_dem_resolution(dem_directory, expected_x_res, expected_y_res):
            logger.info("DEM resolution validation failed.")
            return
        logger.info("DEM resolution validation successful.")

        dem_bbox = box(*DataUtils.get_bbox_from_input(dem_directory))
        landuse_bbox = box(*DataUtils.get_bbox_from_input(landuse_path))
        road_bbox = box(*DataUtils.get_bbox_from_input(road_path))

        logger.debug(f"DEM bbox: {dem_bbox.bounds}")
        logger.debug(f"Landuse bbox: {landuse_bbox.bounds}")
        logger.debug(f"Road bbox: {road_bbox.bounds}")

        bboxes_to_check = [dem_bbox, landuse_bbox, road_bbox]

        clipping_bbox = None
        if optional_clipping_boundary:
            optional_bbox = box(*DataUtils.get_bbox_from_input(optional_clipping_boundary))
            coverage_percentage = DataUtils.get_intersection_percentage(optional_bbox, bboxes_to_check)
            logger.info(f"Optional bounding box covers {coverage_percentage:.2f}% of the total intersection.")
            clipping_bbox =  optional_bbox
        else:
            intersection_bbox = bboxes_to_check[0]
            for bbox in bboxes_to_check[1:]:
                intersection_bbox = intersection_bbox.intersection(bbox)
            clipping_bbox = intersection_bbox
            logger.debug(f"Intersection bbox of datasets: {intersection_bbox.bounds}")
        
        bboxes_to_check.append(clipping_bbox)
        if not DataUtils._validate_overlap(bboxes_to_check):
            logger.info("Overlap validation failed.")
            return
        logger.info("Overlap validation successful.")
        
        
        logger.info("Validation successful! Please close the map to continue...")
        
        
        landuse_crs = gpd.read_file(landuse_path).crs
        DataUtils.plot_bboxes(dem_bbox, landuse_bbox, road_bbox, clipping_bbox,crs = landuse_crs)
        
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
        fig, ax = plt.subplots(figsize=(8, 8))
        for _, row in gdf.iterrows():
            gdf[gdf['label'] == row['label']].plot(ax=ax, color=row['color'], edgecolor=row['color'], hatch=row['hatch'], alpha=0.2)
        
        # For the legend:
        handles = [Patch(facecolor=row['color'], edgecolor='black', hatch=row['hatch'], label=row['label'], alpha=0.5) for _, row in gdf.iterrows()]
        ax.legend(handles=handles, loc="upper left")
        ax.set_title("Bounding boxes. Please close this window to continue.")
        
        if not SUPPRESS_PLOTS:
            plt.show()

    def write_metadata(z_scale, clipping_bbox, expected_x_res=2.0, expected_y_res=2.0, output_folder="data/unreal_tiles/"):
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
        logger.info("Writing metadata...")
        x_scale = expected_x_res * 100
        y_scale = expected_y_res * 100

        metadata = {
            "x_scale": x_scale,
            "y_scale": y_scale,
            "z_scale": z_scale,
            "geo_bbox": {
                # Georeferenced clipping bbox
                "xmin": clipping_bbox.bounds[0],
                "ymin": clipping_bbox.bounds[1],
                "xmax": clipping_bbox.bounds[2],
                "ymax": clipping_bbox.bounds[3]
            }
        }
        logger.info("Metadata generated successfully!")
        with open(os.path.join(output_folder, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

    def check_overlay_directory(overlay_data_directory):
        if not os.path.exists(overlay_data_directory):
            logger.warning(f"Directory {overlay_data_directory} not found. Continuing without generating overlay data...")
            return False

        if not os.listdir(overlay_data_directory):
            logger.error("Overlay data directory is empty.")
            return False
        
        all_files = os.listdir(overlay_data_directory)
        shapefiles = [f for f in all_files if f.endswith('.shp') or f.endswith('.SHP')]

        if len(shapefiles) == 0:
            logger.error("No shapefiles found in the directory.")
            return False
        elif len(shapefiles) > 1:
            logger.error("More than one shapefile found in the directory.")
            return False

        return shapefiles[0]

# PROCESSING DEM DATA
class DemToUnreal:
    def merge_dem_tiles(dem_directory, output_directory):
        """
        Merge multiple DEM tiles from a directory into a single mosaic using rasterio.
        
        Parameters:
            dem_directory (str): Directory containing the DEM tiles.
            output_directory (str): Directory where the merged DEM will be saved.
            
        Returns:
            str: Path to the merged DEM.
        """
        output_path = os.path.join(output_directory, 'merged_dem.tif')
        tile_list = [os.path.join(dem_directory, file) for file in os.listdir(dem_directory) if file.endswith('.tif')]
        
        # Read all the DEM tiles into a list
        src_files_to_mosaic = []
        for tif in tile_list:
            src = rasterio.open(tif)
            src_files_to_mosaic.append(src)

        # Merge function returns a single mosaic array and the transformation info
        mosaic, out_trans = merge(src_files_to_mosaic)
        
        # Write the mosaic raster to disk
        with rasterio.open(output_path, 'w', driver='GTiff',
                        height=mosaic.shape[1], width=mosaic.shape[2],
                        count=1, dtype=mosaic.dtype,
                        crs=src.crs,
                        transform=out_trans) as dest:
            dest.write(mosaic)

        # Close the files
        for src in src_files_to_mosaic:
            src.close()

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
        with rasterio.open(dem_path) as ds:
            width, height = ds.width, ds.height

            logger.debug(f"Total DEM dimensions: Width = {width}, Height = {height}")

            # Extract data from DEM
            data = ds.read(1)
            
            # Find the minimum and maximum values in the DEM
            min_value = data.min()
            max_value = data.max()

            # Scale the DEM data from 0 to 65535 (16-bit maximum value)
            scaled_data = ((data - min_value) / (max_value - min_value) * 65535).astype(np.uint16)

            # Create tiles
            tile_row = 0
            for y in range(0, height, cell_resolution):
                logger.debug(f"Processing row {tile_row}. From y={y} to y={y+cell_resolution}. Expected tiles: {width // cell_resolution}")  # Printout 2
                tile_col = 0
                for x in range(0, width, cell_resolution):
                    output_path = os.path.join(os.path.dirname(dem_path), f'Tile_X{tile_col}_Y{tile_row}.png')
                    
                    # Extract a subset of data for this tile
                    data_subset = scaled_data[y:y+cell_resolution, x:x+cell_resolution]
                    logger.debug(f"  Processing col {tile_col}. From x={x} to x={x+cell_resolution}. Data subset shape: {data_subset.shape}")  # Printout 3

                    # Pad data_subset to desired shape if needed
                    pad_height = cell_resolution - data_subset.shape[0]
                    pad_width = cell_resolution - data_subset.shape[1]
                    data_padded = np.pad(data_subset, 
                                        pad_width=((0, pad_height), 
                                                    (0, pad_width)), 
                                        mode='constant', 
                                        constant_values=0)
                    
                    # Define transform for this subset
                    transform = from_origin(ds.transform.c * x, ds.transform.f * (y + cell_resolution), ds.res[0], ds.res[1])

                    # Write the padded data to a new file
                    with rasterio.open(output_path, 'w', driver='PNG', height=cell_resolution, width=cell_resolution, count=1, 
                                    dtype=np.uint16, transform=transform, crs=ds.crs) as dest:
                        dest.write(data_padded, 1)
                    
                    tile_col += 1
                tile_row += 1

    def calculate_z_scale(dem_path):
        """
        Calculate the Z scale for Unreal Engine based on the DEM data using rasterio.
        
        Parameters:
            dem_path (str): Path to the DEM geotiff file.
            
        Returns:
            float: Calculated Z scale.
        """
        with rasterio.open(dem_path) as ds:
            # Read the first band of the raster
            band_data = ds.read(1)
            
            # Compute the minimum and maximum values of the raster band
            min_value, max_value = band_data.min(), band_data.max()

            # Taking the highest absolute elevation difference (in case of depressions)
            max_abs_difference = max(abs(min_value), abs(max_value))

            # Conversion to centimeters
            max_height_cm = max_abs_difference * 100
            # Possible division here depends on how Unreal reads the PNG-data.
            # Seems it is imported as spanning -256 - 256. Should be the span, 512, that matters here.
            z_scale = max_height_cm / 512.0

        return z_scale

    def resample_dem(dem_path, target_resolution=CELL_RESOLUTION):
        """
        Resample DEM to the target resolution using rasterio.
        
        Parameters:
            dem_path (str): Path to the DEM geotiff file.
            target_resolution (float): The desired resolution in ground units (e.g., 1 for 1m).
            
        Returns:
            str: Path to the resampled DEM.
        """
        logger.info("Resampling DEM...")
        output_path = dem_path.replace('.tif', '_resampled.tif')

        # Open the DEM raster
        with rasterio.open(dem_path) as ds:
            # Calculate the new shape based on the target resolution
            height = int(ds.height * ds.res[0] / target_resolution)
            width = int(ds.width * ds.res[1] / target_resolution)

            # Read the data and resample
            data = ds.read(
                out_shape=(ds.count, height, width),
                resampling=Resampling.bilinear
            )

            # Adjust the metadata
            transform = ds.transform * ds.transform.scale(
                (ds.width / data.shape[-1]),
                (ds.height / data.shape[-2])
            )

            # Write the resampled data to the output path
            with rasterio.open(output_path, 'w',
                            driver='GTiff',
                            height=height,
                            width=width,
                            count=ds.count,
                            dtype=data.dtype,
                            crs=ds.crs,
                            transform=transform) as out_ds:
                out_ds.write(data)

        return output_path


    def generate_heightmap(dem_path, clipping_boundary=None, output_folder="data", ue_cell_resolution=UE_CELL_RESOLUTION):
        logger.info(f"Generating heightmap using DEM at {dem_path} and ue_cell_resolution {ue_cell_resolution}...")
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
            dem_path = DemToUnreal.merge_dem_tiles(dem_path, dem_output_dir)

        # Resample the merged DEM
        dem_path = DemToUnreal.resample_dem(dem_path)

        # Clip the raster using the specified boundary, if provided
        if clipping_boundary:
            dem_path = DemToUnreal.clip_raster_with_boundary(dem_path, clipping_boundary)

        # Calculate the Z scale for the DEM data
        z_scale = DemToUnreal.calculate_z_scale(dem_path)

        # Move the processed DEM to DEM output directory and update dem_path to point to its new location
        new_dem_path = os.path.join(dem_output_dir, os.path.basename(dem_path))
        shutil.move(dem_path, new_dem_path)
        dem_path = new_dem_path

        # Divide the raster into tiles of the specified resolution and save in unreal_tiles directory
        DemToUnreal.divide_raster_into_tiles(dem_path, ue_cell_resolution)

        # delete merge_dem.tif and merged_dem_resampled.tif from dem_output_dir
        os.remove(os.path.join(dem_output_dir, "merged_dem.tif"))
        os.remove(os.path.join(dem_output_dir, "merged_dem_resampled.tif"))

        # Return the Z scale value
        return z_scale


# PROCESSING LANDUSE DATA AND ROAD DATA
class OverlayToUnreal:
    def divide_rasterio_raster_into_tiles(src, cell_resolution, output_directory, return_bbox=False):
        """
        Divide the provided rasterio raster dataset into tiles based on the provided cell resolution.
        
        Parameters:
            src (rasterio.Dataset): Input rasterio dataset or MemoryFile.
            cell_resolution (int): Desired resolution of each cell (tile size).
            output_directory (str): Directory where the tiles will be saved.
            return_bbox (bool, optional): If set to True, returns the bounding box of the tiles.
        
        Returns:
            Polygon or None: Bounding box of the full tiles if return_bbox is True, otherwise None.
        """
        if src is None:
            raise ValueError("Provided rasterio raster dataset is None.")

        width, height = src.width, src.height
        min_val, max_val = src.read(1).min(), src.read(1).max()  # Read the first band
        
        # Define the target min and max based on Unreal's range
        target_min, target_max = 0, 255
        
        # Now loop over the raster to divide it into tiles and rescale the values
        tile_row = 0
        for y in range(0, height, cell_resolution):
            tile_col = 0
            for x in range(0, width, cell_resolution):
                window = rasterio.windows.Window(x, y, cell_resolution, cell_resolution)
                data = src.read(1, window=window)
                
                # Rescale values
                data_rescaled = target_min + ((data - min_val) / (max_val - min_val)) * (target_max - target_min)
                        
                # Pad data_rescaled to desired shape if needed
                pad_height = cell_resolution - data_rescaled.shape[0]
                pad_width = cell_resolution - data_rescaled.shape[1]
                data_padded = np.pad(data_rescaled, 
                                    pad_width=((0, pad_height), 
                                                (0, pad_width)), 
                                    mode='constant', 
                                    constant_values=0)
                                
                # Save as PNG
                output_path = os.path.join(output_directory, f'Tile_X{tile_col}_Y{tile_row}.png')
                with rasterio.open(output_path, 'w', driver='PNG', width=cell_resolution, height=cell_resolution, count=1, dtype='uint8') as dst:
                    dst.write(data_padded.astype('uint8'), 1)
                
                tile_col += 1
            tile_row += 1

        if return_bbox:
            # Return the bounding box as a shapely Polygon
            bounds = src.bounds
            return Polygon([(bounds.left, bounds.bottom), (bounds.left, bounds.top), (bounds.right, bounds.top), (bounds.right, bounds.bottom)])
        
        return None

    def rasterize_landuse(subtracted, cell_resolution, category, clipping_boundary=None):
        """
        Rasterize the subtracted land use data.
        """
        logger.info(f"Rasterizing landuse data for category {category}...")
        if clipping_boundary:
            bounds = clipping_boundary.bounds
        else:
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

    def create_rasterio_raster_from_array(array, transform, output_dir, epsg=None, nodata=None):
        """
        Create a rasterio raster dataset from a numpy array.
        
        Parameters:
            array (numpy.ndarray): The array to be converted to a raster.
            transform (affine.Affine): The affine transformation for the raster.
            output_path (str, optional): The path where the raster should be saved. If None, creates an in-memory raster.
            epsg (int, optional): The EPSG code for the raster's projection. Defaults to 4326 (WGS84).
            nodata (int or float, optional): The NoData value for the raster. If None, no NoData value is set.
        
        Returns:
            rasterio.io.DatasetWriter or rasterio.io.MemoryFile: The rasterio raster dataset.
        """
        
        # Ensure the array is of type byte
        if array.dtype != np.uint8:
            array = np.clip(array, 0, 255).astype(np.uint8)

        profile = {
            "driver": 'GTiff',
            "height": array.shape[0],
            "width": array.shape[1],
            "count": 1,
            "dtype": array.dtype,
            "crs": CRS.from_epsg(epsg if epsg else 4326),
            "transform": transform,
            "compress": 'lzw',
        }

        if nodata is not None:
            profile["nodata"] = nodata

        output_path = os.path.join(output_dir,"blurred_raster_temp")
        with rasterio.open(output_path, "w", **profile) as dest:
            dest.write(array, 1)
        return rasterio.open(output_path)

    def blur_raster_array(raster_array, transform,output_dir,epsg = None):
        """
        Blur the rasterized land use data provided as a numpy array.
        """
        logger.info("Blurring raster array...")
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

        blurred_rasterio_object = OverlayToUnreal.create_rasterio_raster_from_array(blurred, transform, output_dir, epsg = epsg)
        return blurred_rasterio_object


    def generate_land_use_mask(landuse_vector_path,
                            road_vector_path,
                            clipping_boundary,
                            landuse_mapping=LANDUSE_MAPPING,
                            road_buffer_dict=BUFFER_DICT,
                            cell_resolution=CELL_RESOLUTION,
                            ue_cell_resolution=UE_CELL_RESOLUTION,
                            output_dir="data/unreal_tiles"):
        logger.info("Generating land use mask...")
        landuse = gpd.read_file(landuse_vector_path)
        roads = gpd.read_file(road_vector_path)
        epsg = DEFAULT_EPSG if landuse.crs.to_epsg() is None else landuse.crs.to_epsg()

        # Clip the landuse and road data using the optional clipping boundary, if provided
        logger.debug(f"Initial landuse data bounds: {landuse.total_bounds}")
        logger.debug(f"Initial roads data bounds: {roads.total_bounds}")
        logger.debug(f"Clipping boundary bounds: {clipping_boundary.bounds}")

        clipping_gdf = gpd.GeoDataFrame({'geometry': [clipping_boundary]})
        clipping_gdf.set_crs(landuse.crs, inplace=True)
        landuse = gpd.clip(landuse, clipping_gdf)
        roads = gpd.clip(roads, clipping_gdf)

        logger.debug(f"Landuse data bounds after clipping: {landuse.total_bounds}")
        logger.debug(f"Roads data bounds after clipping: {roads.total_bounds}")

        # Buffer roads
        roads['geometry'] = roads.apply(lambda row: row['geometry'].buffer(road_buffer_dict.get(row[ROAD_CATEGORY_VARIABLE], DEFAULT_ROAD_BUFFER)), axis=1)
        buffered_roads = roads.dissolve()

        logger.debug(f"Number of unique road types: {roads[ROAD_CATEGORY_VARIABLE].nunique()}")
        logger.debug(f"Unique road types: {roads[ROAD_CATEGORY_VARIABLE].unique()}")
        logger.debug(f"Buffered roads bounds: {buffered_roads.total_bounds}")

        # Write roads first
        category_dir = os.path.join(output_dir, 'ROAD')
        os.makedirs(category_dir, exist_ok=True)
        raster, transform = OverlayToUnreal.rasterize_landuse(buffered_roads, cell_resolution, 'ROAD',clipping_boundary)
        blurred_raster = OverlayToUnreal.blur_raster_array(raster, transform, category_dir, epsg)

        logger.debug(f"Raster shape: {raster.shape}")
        logger.debug(f"Transform: {transform}")

        # Tile the blurred raster
        landuse_clipping_bbox = OverlayToUnreal.divide_rasterio_raster_into_tiles(blurred_raster, ue_cell_resolution, category_dir, return_bbox = True)

        logger.debug(f"Bounds of the rasterized and blurred roads: {landuse_clipping_bbox}")
        logger.debug(f"Min, Max values of raster: {raster.min()}, {raster.max()}")
        logger.debug(f"Unique values in raster: {np.unique(raster)}")

        # Initialize the plotting area outside the loop
        fig, ax = plt.subplots(figsize=(12, 12))
        legend_patches = []

        # If you have a predefined set of categories, you can manually specify colors:
        # colors = {"CATEGORY1": "red", "CATEGORY2": "green", "CATEGORY3": "blue", ...}
        colors = {
        "WATER": "#a5bfdd",      # Pastel turquoise
        "BUILDINGS": "#707070",  # Pastel red/pink
        "FARMING": "#739268",       # Pastel orange
        "OPEN AREAS": "#8fb583", # Pastel purple/lavender
        "FOREST": "#94d180"      # Pastel green
        }   

        #cmap = plt.get_cmap("tab10")  # 10 distinct colors
        #colors = {category: cmap(i) for i, category in enumerate(landuse_mapping.keys())}
        # Alpha value for transparency
        alpha_value = 0.8



        for category, details in landuse_mapping.items():
            combined_features = landuse[landuse[LANDUSE_CATEGORY_VARIABLE].isin(details)]

            if combined_features.empty:
                logger.info(f"No features found for category {category}. Skipping...")
                continue

            # Subtract buffered road network
            subtracted = gpd.overlay(combined_features, buffered_roads, how="difference")
            
            # Plot the subtracted data
            color_for_this_category = colors[category]
            subtracted.plot(ax=ax, color=color_for_this_category, alpha=alpha_value)
            # Create a custom patch for the legend and add to the list
            legend_patches.append(mpatches.Patch(color=color_for_this_category, label=f'{category} Subtracted Data', alpha=alpha_value))

            logger.info(f"Processing category {category} with {len(subtracted)} features.")

            # Rasterize the subtracted data
            category_dir = os.path.join(output_dir, category)
            os.makedirs(category_dir, exist_ok=True)

            raster, transform = OverlayToUnreal.rasterize_landuse(subtracted, cell_resolution, category,clipping_boundary)
            blurred_raster = OverlayToUnreal.blur_raster_array(raster, transform, category_dir, epsg)

            # Tile the blurred raster
            OverlayToUnreal.divide_rasterio_raster_into_tiles(blurred_raster, ue_cell_resolution, category_dir)
        
        # Plot the clipping boundary once, outside the loop
        gpd.GeoSeries([clipping_boundary], crs=landuse.crs).plot(ax=ax, color='none', edgecolor='blue')

        # Add the clipping boundary to the legend
        legend_patches.append(mpatches.Patch(edgecolor='blue', facecolor='none', label='Clipping Boundary', alpha=alpha_value))

        # Set title, labels, and add the legend using the custom patches
        ax.set_title(f"Land Use Categories. Please close this window to continue.")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.legend(handles=legend_patches, loc="upper left", bbox_to_anchor=(1,1), borderaxespad=0.)
        plt.tight_layout()
        if not SUPPRESS_PLOTS:
            plt.show()
        return landuse_clipping_bbox

    def load_and_reproject_data(overlay_data_directory, shapefile_name, landuse_path):
        gdf = gpd.read_file(os.path.join(overlay_data_directory, shapefile_name))

        landuse_crs = gpd.read_file(landuse_path).crs
        if not gdf.crs == landuse_crs:
            logger.warning("Overlay data crs is not same as landuse crs. Reprojecting...")
            gdf = gdf.to_crs(landuse_crs)
            logger.info("Reprojection successful!")
        
        return gdf

    def plot_and_save_overlay(gdf, clipping_boundary, value_column):
        # Set up the figure and ax based on the clipping boundary
        clipping_bbox = clipping_boundary.bounds
        clipping_width = clipping_bbox[2] - clipping_bbox[0]
        clipping_height = clipping_bbox[3] - clipping_bbox[1]
        clipping_aspect_ratio = clipping_width / clipping_height

        fig_height = 8
        fig_width = fig_height * clipping_aspect_ratio
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        ax.set_aspect('equal')
        ax.set_xlim(clipping_bbox[0], clipping_bbox[2])
        ax.set_ylim(clipping_bbox[1], clipping_bbox[3])

        # Create a base array for alpha (all zeros, i.e., fully transparent)
        alpha_array = np.zeros_like(gdf[value_column].values, dtype=float)
        
        # Set alpha to 1 (opaque) where data exists
        alpha_array[~gdf[value_column].isna()] = 1.0
        
        # Normalize the data for coloring
        min_val = gdf[value_column].min()
        max_val = gdf[value_column].max()
        if min_val >= 0:
            norm = mcolors.Normalize(vmin=0, vmax=max_val)
        else:
            norm = mcolors.Normalize(vmin=min_val, vmax=max_val)
        
        # Plotting with custom cmap and alpha
        colors = plt.cm.gray(norm(gdf[value_column].values))
        colors[:, 3] = alpha_array  # Set the alpha channel based on our mask
        
        gdf.plot(facecolor=colors, ax=ax, edgecolor='none')
        
        ax.axis('off')
        plt.tight_layout(pad=0)
        ax.set_facecolor('none')
        fig.set_facecolor('none')
        
        # Save the plot
        output_directory = os.path.join('data', 'unreal_tiles', 'OVERLAY')
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        output_path = os.path.join(output_directory, 'output_plot.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
        
        plt.close()

        return output_path

    def generate_overlay_data(overlay_data_directory, clipping_boundary, landuse_path):
        plt.close('all')  # Close previous plots
        logger.info("Generating overlay data...")

        shapefile_name = DataUtils.check_overlay_directory(overlay_data_directory)
        if not shapefile_name:
            return

        gdf = OverlayToUnreal.load_and_reproject_data(overlay_data_directory, shapefile_name, landuse_path)
        if not gdf.geometry.intersects(clipping_boundary).any():
            logger.error("Overlay data does not intersect with clipping boundary.")
            return
        
        gdf = gpd.clip(gdf, clipping_boundary)
        value_column = [col for col in gdf.columns if col != 'geometry'][0]
        output_path = OverlayToUnreal.plot_and_save_overlay(gdf, clipping_boundary, value_column)
        
        logger.info(f"Overlay data saved to {output_path}")
        logger.info(f"Plot saved to {output_path}")

def generate_unreal_tiles(dem_directory, landuse_path, road_path,overlay_data_directory = None):
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
    DataUtils.check_and_clear_data()
    
    logger.info("Generating Unreal tiles...")
    # Validate input data
    clipping_bbox = DataUtils.validate_input_data(dem_directory, landuse_path, road_path)
    
    # Generate heightmap
    z_scale = DemToUnreal.generate_heightmap(dem_directory, clipping_boundary=clipping_bbox)
    # Generate land use mask
    landuse_clipping_bbox = OverlayToUnreal.generate_land_use_mask(landuse_path, road_path, clipping_boundary=clipping_bbox)

    if overlay_data_directory:
        # Generate overlay data
        OverlayToUnreal.generate_overlay_data(overlay_data_directory, clipping_bbox, landuse_path)
    
    # Write metadata
    DataUtils.write_metadata(z_scale, clipping_bbox)

    tile_xmin, tile_ymin, tile_xmax, tile_ymax = clipping_bbox.bounds

    # Setup for generating buildings
    data_directory = os.path.join('data', 'unreal_buildings')
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
    stl_path = generate_builder_buildings(data_directory , LIDAR_DIRECTORY, BUILDING_SHAPEFILE_PATH, clipping_bbox = clipping_bbox, unreal_resolution = UE_CELL_RESOLUTION, cell_resolution = CELL_RESOLUTION)

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Unreal Tile Generator")
parser.add_argument("--no-plots", action="store_true", help="Suppress plots.")

if __name__ == "__main__":
    # Set logging level
    logger.setLevel(logging.INFO)

    # Define input paths
    DEM_DIRECTORY = "data\\dem_data"
    LANDUSE_PATH = "data\\landuse_data\\my_south.shp"
    ROAD_PATH = "data\\road_data\\vl_riks.shp"
    OVERLAY_PATH = "data\\overlay_data\\"
    LIDAR_DIRECTORY = "data\\lidar_data\\"
    BUILDING_SHAPEFILE_PATH = "data\\footprint_data\\by_04.shp"

    args = parser.parse_args()
    # Supress plots based on command-line argument
    SUPPRESS_PLOTS = args.no_plots

    # Call the function
    generate_unreal_tiles(DEM_DIRECTORY, LANDUSE_PATH, ROAD_PATH, OVERLAY_PATH)