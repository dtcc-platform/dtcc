# Copyright (C) 2023 Sanjay Somanath
# Licensed under the GPL License # TODO: Double check this with DTCC
# This script documents the workflow for dtcc builder geojson to IDF/GBXML/DFJSON.

# Attribution
# This work incorporates code from the Ladybug Tools project (https://github.com/ladybug-tools), 
# which is licensed under the GNU General Public License (GPL) Version 3. 
# Any derivative works must also be released under an open source GPL license.

import argparse
import json
import logging
import os
from math import ceil
import geopandas as gpd
from ladybug.futil import preparedir
from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.face import Face3D
from dragonfly.model import Model
from dragonfly.building import Building
from dragonfly.story import Story
from dragonfly.room2d import Room2D
from dragonfly.windowparameter import SimpleWindowRatio, RepeatingWindowRatio
from honeybee_energy.lib.programtypes import office_program, ProgramType
from honeybee_energy.run import add_gbxml_space_boundaries, to_openstudio_osw, to_gbxml_osw, run_osw,_face_to_gbxml_geo
from honeybee.model import Model as HBModel
from honeybee.config import folders as hb_folders
from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.writer import energyplus_idf_version
import xml.etree.ElementTree as ET
import re
import shutil
import traceback
import honeybee_energy_standards # To check that the standards are installed
from honeybee_energy.lib.constructionsets import construction_set_by_identifier
from honeybee_energy.lib._loadprogramtypes import _program_types_standards_registry as STANDARDS_REGISTRY


#import pdb; pdb.set_trace()

#__name__ = 'workflow_geojson_to_DF'
# Set up the logger
logging.basicConfig(level=logging.INFO)
# Create a custom logger with name 'geojson_to_DF'
logger = logging.getLogger('geojson_to_DF')
# Constants

DEFAULT_CLIMATE_ZONE = 'ClimateZone6'  # 'ClimateZone1', 'ClimateZone2', 'ClimateZone3', 'ClimateZone4', 'ClimateZone5', 'ClimateZone6', 'ClimateZone7'
DEFAULT_CONSTRUCTION_TYPE = 'Mass' #'SteelFramed', 'WoodFramed', 'Mass', 'Metal Building'
DEFAULT_YEAR = 2000
PROJECT_NAME = 'City'
FLOOR_TO_FLOOR_HEIGHT = 2.8
WINDOW_TO_WALL_RATIO = 0.4
WINDOW_HEIGHT = 1.6
WINDOW_SILL_HEIGHT = 0.7
WINDOW_TO_WINDOW_HORIZONTAL_SPACING = 4
ADD_DEFAULT_IDEAL_AIR = True
DEFAULT_PROGRAM = ProgramType('HighriseApartment')
BUILDING_PROGRAM_DICT = {
    "Bostad; Småhus friliggande": "HighriseApartment",
    "Bostad; Småhus kedjehus": "MidriseApartment",
    "Bostad; Småhus radhus": "MidriseApartment",
    "Bostad; Flerfamiljshus": "HighriseApartment",
    "Bostad; Småhus med flera lägenheter": "MidriseApartment",
    "Bostad; Ospecificerad": "HighriseApartment",
    "Industri; Annan tillverkningsindustri": "Warehouse",
    "Industri; Gasturbinanläggning": "LargeDataCenterHighITE",
    "Industri; Industrihotell": "LargeHotel",
    "Industri; Kemisk industri": "Laboratory",
    "Industri; Kondenskraftverk": "Warehouse",
    "Industri; Kärnkraftverk": "LargeDataCenterHighITE",
    "Industri; Livsmedelsindustri": "SuperMarket",
    "Industri; Metall- eller maskinindustri": "Warehouse",
    "Industri; Textilindustri": "Warehouse",
    "Industri; Trävaruindustri": "Warehouse",
    "Industri; Vattenkraftverk": "Warehouse",
    "Industri; Vindkraftverk": "Warehouse",
    "Industri; Värmeverk": "Warehouse",
    "Industri; Övrig industribyggnad": "Warehouse",
    "Industri; Ospecificerad": "Warehouse",
    "Samhällsfunktion; Badhus": "Outpatient",
    "Samhällsfunktion; Brandstation": "SmallOffice",
    "Samhällsfunktion; Busstation": "SmallOffice",
    "Samhällsfunktion; Distributionsbyggnad": "Warehouse",
    "Samhällsfunktion; Djursjukhus": "Outpatient",
    "Samhällsfunktion; Försvarsbyggnad": "Courthouse",
    "Samhällsfunktion; Vårdcentral": "Outpatient",
    "Samhällsfunktion; Hälsocentral": "Outpatient",
    "Samhällsfunktion; Högskola": "SecondarySchool",
    "Samhällsfunktion; Ishall": "SmallOffice",
    "Samhällsfunktion; Järnvägsstation": "SmallOffice",
    "Samhällsfunktion; Kommunhus": "Courthouse",
    "Samhällsfunktion; Kriminalvårdsanstalt": "Courthouse",
    "Samhällsfunktion; Kulturbyggnad": "SmallOffice",
    "Samhällsfunktion; Polisstation": "SmallOffice",
    "Samhällsfunktion; Reningsverk": "SmallDataCenterHighITE",
    "Samhällsfunktion; Ridhus": "SmallOffice",
    "Samhällsfunktion; Samfund": "SmallOffice",
    "Samhällsfunktion; Sjukhus": "Hospital",
    "Samhällsfunktion; Skola": "PrimarySchool",
    "Samhällsfunktion; Sporthall": "SmallOffice",
    "Samhällsfunktion; Universitet": "SecondarySchool",
    "Samhällsfunktion; Vattenverk": "SmallDataCenterHighITE",
    "Samhällsfunktion; Multiarena": "SmallOffice",
    "Samhällsfunktion; Ospecificerad": "SmallOffice",
    "Verksamhet; Ospecificerad": "SmallOffice",
    "Ekonomibyggnad; Ospecificerad": "Warehouse",
    "Komplementbyggnad; Ospecificerad": "SmallOffice",
    "Övrig byggnad; Ospecificerad": "SmallOffice"
}
# from honeybee_energy.lib import programtypes 
# programtypes.BUILDING_TYPES to see other options

 #'SmallDataCenterHighITE',
 #'QuickServiceRestaurant',
 #'Outpatient',
 #'HighriseApartment',
 #'LargeHotel',
 #'SmallOffice',
 #'MediumOffice',
 #'Courthouse',
 #'LargeOffice',
 #'Warehouse',
 #'Retail',
 #'SmallHotel',
 #'SuperMarket',
 #'LargeDataCenterLowITE',
 #'Hospital',
 #'Laboratory',
 #'PrimarySchool',
 #'LargeDataCenterHighITE',
 #'MidriseApartment',
 #'StripMall',
 #'SmallDataCenterLowITE',
 #'SecondarySchool',
 #'FullServiceRestaurant'



# 1. Load the GeoJSON Data
def load_geojson_data(filepath):
    """
    Load the GeoJSON data from the provided file path.

    :param filepath: Path to the geojson file.
    :return: Loaded GeoJSON data.
    """
    # Check if clip.geojson exists
    if os.path.isfile('clip.geojson'):
        logger.info("clip.geojson found. Setting the buildings outside the clip area as context...")
        clip_gdf = gpd.read_file('clip.geojson')
        # load the geojson file at filepath
        gdf = gpd.read_file(filepath)
        # Count the number of buildings in the GeoDataFrame
        logger.info(f"Number of buildings before clipping: {len(gdf)}")
        # Set the building_status to 'context' for buildings outside the clip area
        gdf.loc[~gdf.intersects(clip_gdf.unary_union), 'building_status'] = 'Existing'
        # Count the number of buildings set to 'Existing' as context and 'Building' as buildings
        len_existing = len(gdf[gdf['building_status'] == 'Existing'])
        len_building = len(gdf[gdf['building_status'] == 'Building'])
        logger.info(f"Number of buildings set to 'Existing' as context: {len_existing}")
        logger.info(f"Number of buildings set to 'Building' as buildings: {len_building}")
        # Save the GeoDataFrame to a new GeoJSON file
        gdf.to_file(filepath, driver='GeoJSON')

    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def filter_buildings(city_geojson_path, new_city_geojson_path, filter_height_less_than = 3, filter_height_greater_than = 100, filter_area_less_than = 100 ):
    """ Filter out buildings with height less than 3 meters or more than 100 meters
        and area less than 100 square meters. 
    """
    print(f"city_geojson_path: {city_geojson_path}")
    print(f"new_city_geojson_path: {new_city_geojson_path}")
    print(f"filter_height_less_than: {filter_height_less_than}")
    print(f"filter_height_greater_than: {filter_height_greater_than}")
    print(f"filter_area_less_than: {filter_area_less_than}")

    logger.info("Copying the geojson file...")
    # Copy the original geojson file to the new path
    shutil.copyfile(city_geojson_path, new_city_geojson_path)

    # Load the GeoDataFrame
    gdf = gpd.read_file(new_city_geojson_path)

    features_before = len(gdf)
    logger.info(f"Filtering out buildings with height less than 3 meters or more than 100 meters...")
    # Filter out buildings with height less than 3 meters or more than 100 meters
    gdf = gdf[(gdf['height'] > filter_height_less_than) & (gdf['height'] < filter_height_greater_than)]

    # Convert CRS to EPSG 3006 to calculate area in square meters
    gdf = gdf.to_crs(crs='3006')
    gdf["area_sqm"] = gdf.geometry.area
    logger.info(f"Filtering out buildings with area less than 100 square meters...")
    # Filter out buildings with area less than 100 square meters 
    gdf = gdf[gdf['area_sqm'] >= filter_area_less_than]

    # Convert CRS back to EPSG 4326
    gdf = gdf.to_crs(crs='4326')

    # Drop the 'area_sqm' column
    gdf = gdf.drop(columns=['area_sqm'])

    # Save the GeoDataFrame to a new GeoJSON file
    gdf.to_file(new_city_geojson_path, driver='GeoJSON')
    features_after = len(gdf)
    logger.info(f"Filtered out {features_before - features_after} buildings")


def enrich_city_geojson(city_geojson_path):
    with open(city_geojson_path, 'r', encoding='utf-8') as file:
        city_geojson = json.load(file)
    # Get the bounding box of the city
    city_gdf = gpd.read_file(city_geojson_path)
    city_bounds = city_gdf.bounds
    lon_min,lat_min  = city_bounds.minx.min(), city_bounds.miny.min()
    project = {"project": {
        "id": PROJECT_NAME,
        "name": PROJECT_NAME,
        "latitude": lat_min,
        "longitude": lon_min
    }}
    print(f"lat_min: {lat_min}, lon_min: {lon_min}")
    # Add project to city_json
    city_geojson.update(project)
    # Create the project object
    
    # Add project to city_json
    city_geojson.update(project)
    # Adding building properties
    for i, building in enumerate(city_geojson['features']):
        properties = building["properties"]
        height = properties["height"]
        number_of_stories = ceil(height/FLOOR_TO_FLOOR_HEIGHT)
        properties["id"] = "Building{}".format(i)
        properties["name"] = "Building{}".format(i)
        properties["building_status"] = "Building"
        properties["type"] = "Building"
        properties["maximum_roof_height"] = height
        properties["number_of_stories"] = number_of_stories
        properties["window_to_wall_ratio"] = WINDOW_TO_WALL_RATIO
    # Write city_json to file
    # Write city_json to file using UTF-8 encoding with indentation
    with open(city_geojson_path, "w", encoding='utf-8') as f:
        json.dump(city_geojson, f, ensure_ascii=False, indent=4)
    return city_geojson_path
def get_closest_standard_year(input_year):
    """
    Return the closest year or range from STANDARDS_REGISTRY for the given input year.
    """
    
    # Convert the input_year to an integer
    input_year = int(input_year)
    
    # Check if the input year is less than 1900
    if input_year < 1900:
        raise ValueError("Year must be 1900 or later.")
    
    # A dictionary to convert special values in STANDARDS_REGISTRY to representative numbers for comparison
    conversion = {
        'pre_1980': 1979,
        '1980_2004': 1980
    }
    
    # Convert years in STANDARDS_REGISTRY to integers for comparison
    years = []
    for yr in STANDARDS_REGISTRY.keys():
        if yr in conversion:
            years.append(conversion[yr])
        else:
            try:
                years.append(int(yr))
            except ValueError:
                pass  # ignore if cannot be converted
    
    # Get the difference between input_year and each year in STANDARDS_REGISTRY
    differences = [abs(input_year - yr) for yr in years]
    
    # Get the closest year
    closest_year_key = list(STANDARDS_REGISTRY.keys())[differences.index(min(differences))]

    return closest_year_key
def get_construction_identifier(construction_type, climate_zone, year):
    """
    Return the construction identifier for the given construction type, climate zone, and year.
    """
        
    # Get the closest year from STANDARDS_REGISTRY
    closest_year = get_closest_standard_year(year)
    
    construction_identifier = f"{closest_year}::{climate_zone}::{construction_type}"
    
    return construction_identifier
def adjust_building_properties(model, geojson_object):
    """
    Adjust properties of buildings in the model using provided building heights.

    """
    # If building_status is 'Building' keep it in building_object if not move it to context_object
    building_objects = [bldg for bldg in geojson_object['features'] if bldg["properties"]["building_status"] == "Building"]
    context_objects = [bldg for bldg in geojson_object['features'] if bldg["properties"]["building_status"] == "Existing"]
    # Check if the number of buildings in the geojson file matches the number of buildings in the model
    if len(building_objects) != len(model.buildings):
        logger.error(f"Number of buildings in the geojson file: {len(building_objects)}")
        logger.error(f"Number of buildings in the model: {len(model.buildings)}")
        raise Exception("Number of buildings in the geojson file does not match the number of buildings in the model.")
        return
    # Check if the number of buildings in the geojson file matches the number of buildings in the model
    if len(context_objects) != len(model.context_shades):
        logger.error(f"Number of buildings in the geojson file: {len(context_objects)}")
        logger.error(f"Number of buildings in the model: {len(model.context_shades)}")
        raise Exception("Number of buildings in the geojson file does not match the number of buildings in the model.")
        return
    # Move buildings above ground
    for i, building  in enumerate(model.buildings):
        ground_height = building_objects[i]["properties"]['ground_height']
        building_type = building_objects[i]["properties"]['ANDAMAL_1T']
        # Fetch the default construction set, this can be set to any year, construction type and climate zone
        construction_identifier = get_construction_identifier(DEFAULT_CONSTRUCTION_TYPE, DEFAULT_CLIMATE_ZONE, DEFAULT_YEAR)
        construction_set = construction_set_by_identifier(construction_identifier)
        m_vec = Vector3D(0, 0, ground_height)
        building.move(m_vec)
        for storey in building:
            for room in storey.room_2ds:
                #logger.info(f"Setting construction set to {construction_identifier} for building type: {building_type}")
                room.properties.energy.construction_set = construction_set
                building_program = BUILDING_PROGRAM_DICT.get(building_type)
                if building_program is None:
                    print(f"No program found for building type: {building_type}")
                    program = DEFAULT_PROGRAM
                else:
                    program = ProgramType(building_program)
                room.properties.energy.program_type = program
                if ADD_DEFAULT_IDEAL_AIR:
                    room.properties.energy.add_default_ideal_air()
                # Set window parameters for the new storey
                storey.set_outdoor_window_parameters(RepeatingWindowRatio(
                    WINDOW_TO_WALL_RATIO,
                    WINDOW_HEIGHT,
                    WINDOW_SILL_HEIGHT,
                    WINDOW_TO_WINDOW_HORIZONTAL_SPACING
                ))
    # Move context_shades above ground
    for i, context in enumerate(model.context_shades):
        ground_height = context_objects[i]["properties"]['ground_height']
        m_vec = Vector3D(0, 0, ground_height)
        context.move(m_vec)

    return model

# This should not be recreated - available in cli
def model_to_hb_models(model,add_plenum=False,use_multiplier = True):
    """Translate a Model DFJSON to a Honeybee Model."""

    model.convert_to_units('Meters')

    # convert Dragonfly Model to Honeybee
    hb_models = model.to_honeybee(object_per_model='District', shade_distance=None,
                    use_multiplier=use_multiplier, add_plenum=add_plenum, cap=False,
                    solve_ceiling_adjacencies=True, tolerance=None, enforce_adj=False)
    return hb_models[0]

# This should not be recreated - available in cli
def hb_model_to_idf(hb_model, additional_str = '', compact_schedules = True, 
                  hvac_to_ideal_air = True, output_file_path= None):
    """Translate a Honeybee model to an IDF file."""


    # set the schedule directory in case it is needed
    sch_directory = None
    if not compact_schedules:
        sch_path = os.path.abspath(output_file_path)
        sch_directory = os.path.join(os.path.split(sch_path)[0], 'schedules')

    # create the strings for simulation parameters and model
    ver_str = energyplus_idf_version()
    sim_par = SimulationParameter()
    sim_par.output.add_zone_energy_use()
    sim_par.output.add_hvac_energy_use()
    sim_par_str = sim_par.to_idf()
    model_str = hb_model.to.idf(hb_model, schedule_directory=sch_directory, 
                                use_ideal_air_equivalent=hvac_to_ideal_air)
    idf_str = '\n\n'.join([ver_str, sim_par_str, model_str, additional_str])

    # write out the IDF file
    try:
        with open(output_file_path, 'w') as output_file:
            output_file.write(idf_str)
    except Exception as e:
        logger.exception('Model translation failed.\n{}'.format(e))
        raise e
    # If no errors, log the success
    logger.info('Successfully wrote IDF file to: {}'.format(output_file_path))
    return output_file_path

def model_to_gbxml(model_file = None, multiplier = True, no_plenum = True, no_ceil_adjacency= False,
                   osw_folder = None, minimal = False, output_file = None):
    """Translate a Model DFJSON to a gbXML file.

    \b
    Args:
        model_file: Path to either a DFJSON or DFpkl file. This can also be a
            HBJSON or a HBpkl from which a Dragonfly model should be derived.
    """
    try:
        # set the default folder if it's not specified
        out_path = None

        out_directory = os.path.join(
            hb_folders.default_simulation_folder, 'temp_translate')
        f_name = output_file
        f_name = f_name.replace('.gbxml', '.xml')
        preparedir(out_directory)

        # re-serialize the Dragonfly Model
        model = Model.from_dfjson(model_file)
        model.convert_to_units('Meters')

        # convert Dragonfly Model to Honeybee
        add_plenum = not no_plenum
        ceil_adjacency = not no_ceil_adjacency
        hb_models = model.to_honeybee(
            object_per_model='District', use_multiplier=multiplier,
            add_plenum=add_plenum, solve_ceiling_adjacencies=ceil_adjacency)
        hb_model = hb_models[0]

        # create the dictionary of the HBJSON for input to OpenStudio CLI
        for room in hb_model.rooms:
            room.remove_colinear_vertices_envelope(0.01, delete_degenerate=True)
        model_dict = hb_model.to_dict(triangulate_sub_faces=True)
        hb_model.properties.energy.add_autocal_properties_to_dict(model_dict)
        hb_model_json = os.path.abspath(os.path.join(out_directory, 'in.hbjson'))
        with open(hb_model_json, 'w') as fp:
            json.dump(model_dict, fp)
        logger.info('Successfully wrote HBJSON file to: {}'.format(hb_model_json))
        # Write the osw file and translate the model to gbXML
        out_f = out_path if output_file.endswith('-') else output_file
        #make outfile path absolute relative to current directory
        out_f = os.path.abspath(out_f)
        
        osw = to_gbxml_osw(hb_model_json, out_f, osw_folder)
        logger.info('Successfully wrote OSW file to: {}'.format(osw))
        if minimal:
            _run_translation_osw(osw, out_path)
        else:
            _, idf = run_osw(osw, silent=True)
            if idf is not None and os.path.isfile(idf):
                hb_model = HBModel.from_hbjson(hb_model_json)
                logger.info('Writing gbXML file...')
                add_gbxml_space_boundaries(out_f, hb_model)
                logger.info('Successfully wrote gbXML file to: {}'.format(out_f))
                if out_path is not None:  # load the JSON string to stdout
                    with open(out_path) as json_file:
                        print(json_file.read())
            else:
                raise Exception('Running OpenStudio CLI failed.')
    except Exception as e:
        logger.exception('Model translation failed.\n{}'.format(e))


def generate_DF_enriched_geojson(enriched_city_geojson_path, dfModel):
    """
    Expected attributes in the dfModel:
        * height
        * height_above_ground
        * height_from_first_floor
        * footprint_area
        * floor_area
        * exterior_wall_area
        * exterior_aperture_area
        * volume
    """
    # Open geojson file
    with open(enriched_city_geojson_path, 'r', encoding='utf-8') as file:
        city_geojson = json.load(file)

    # Ensure 'features' key is in the geojson
    if "features" not in city_geojson:
        raise ValueError("The geojson does not contain a 'features' key.")
    
    # Filter city_geojson features to get buildings with building_status == 'Building'
    filtered_buildings = [bldg for bldg in city_geojson["features"] if bldg["properties"]["building_status"] == "Building"]  

    # Check if the number of buildings in the geojson file matches the number of buildings in the model
    if len(filtered_buildings) != len(dfModel.buildings):
        logger.error(f"Number of buildings in the geojson file: {len(filtered_buildings)}")
        logger.error(f"Number of buildings in the model: {len(dfModel.buildings)}")
        raise Exception("Number of buildings in the geojson file does not match the number of buildings in the model.")
        return
    
    # Iterate over buildings with building_status == 'Building'
    for i, bldg_object in enumerate(filtered_buildings):
        building = dfModel.buildings[i]
        # Add building properties to the geojson file
        bldg_object["properties"]["height"] = round(building.height, 2)
        bldg_object["properties"]["height_above_ground"] = round(building.height_above_ground, 2)
        bldg_object["properties"]["height_from_first_floor"] = round(building.height_from_first_floor, 2)
        bldg_object["properties"]["footprint_area"] = round(building.footprint_area, 2)
        bldg_object["properties"]["floor_area"] = round(building.floor_area, 2)
        bldg_object["properties"]["exterior_wall_area"] = round(building.exterior_wall_area, 2)
        bldg_object["properties"]["exterior_aperture_area"] = round(building.exterior_aperture_area, 2)
        bldg_object["properties"]["volume"] = round(building.volume, 2)

    # Write city_json to file
    new_city_geojson_path = 'city_enriched_DF.geojson'
    # Write city_json to file using UTF-8 encoding with indentation
    with open(new_city_geojson_path, "w", encoding='utf-8') as f:
        json.dump(city_geojson, f, ensure_ascii=False, indent=4)




# Main execution
def generate_EP_assets(geojson_file_path,use_multiplier = False, generate_DFenriched_geojson = False, filter_height_less_than=3, filter_height_greater_than=100, filter_area_less_than=100):
    logger.info("Starting script execution...")
    # Copy the geojson file
    new_geojson_file_path =  'city_enriched.geojson'
    # Copy the geojson file using shutil.copyfile(src, dst)
    filter_buildings(geojson_file_path, new_geojson_file_path, filter_height_less_than = filter_height_less_than, filter_height_greater_than = filter_height_greater_than, filter_area_less_than = filter_area_less_than)
    enrich_city_geojson(new_geojson_file_path)
    logger.info(f"Loading data from {geojson_file_path}")
    data = load_geojson_data(new_geojson_file_path)
    logger.info("Creating Dragonfly model from GeoJSON...")

    model, location = Model.from_geojson(new_geojson_file_path, location=None, point=Point2D(0, 0),
                     all_polygons_to_buildings=False, existing_to_context=True,
                     units='Meters', tolerance=None, angle_tolerance=1.0)
    logger.info("Adjusting building properties in the model...")
    adjusted_model = adjust_building_properties(model, data)
    
    if generate_DFenriched_geojson:
        generate_DF_enriched_geojson(new_geojson_file_path,adjusted_model)
    current_directory = os.getcwd()
    adjusted_model.to_dfjson('city',current_directory, 2,None)

    logger.info("Serializing the Dragonfly Model to Honeybee Models...")
    hb_model = model_to_hb_models(adjusted_model, add_plenum=False, use_multiplier=use_multiplier)

    logger.info("Converting Honeybee Models to IDF...")
    hb_model_to_idf(hb_model, output_file_path =  'city.idf')
    logger.info("Converting Honeybee Models to GBXML...")
    model_to_gbxml('city.dfjson',multiplier=use_multiplier, output_file='city.gbxml')

    logger.info("Script execution completed!")

import argparse

if __name__ == '__main__':
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Process geojson files in a directory")
    parser.add_argument('--directory_path', type=str, required=True, help='Path to the directory containing geojson file(s)')
    
    parser.add_argument('--multiplier', default=False, action='store_true', help='Flag to use multiplier')
    parser.add_argument('--generate_DFenriched_geojson', default=False, action='store_true', help='Flag to generate DF enriched geojson')
    parser.add_argument('--filter_height_less_than', default = 3,  type=float, help='Filter by height less than specified value')
    parser.add_argument('--filter_height_greater_than', default = 100, type=float, help='Filter by height greater than specified value')
    parser.add_argument('--filter_area_less_than', default = 100, type=float, help='Filter by area less than specified value')
    
    # Parse the arguments
    args = parser.parse_args()
    logger.info(f"Changing directory to {args.directory_path}")
    os.chdir(args.directory_path)
    # Log the arguments
    logger.info(f"generate_DFenriched_geojson: {args.generate_DFenriched_geojson}")
    logger.info(f"filter_height_less_than: {args.filter_height_less_than}")
    logger.info(f"filter_height_greater_than: {args.filter_height_greater_than}")
    logger.info(f"filter_area_less_than: {args.filter_area_less_than}")
    
    # Get the geojson file path
    city_geojson_file_path = os.path.join(args.directory_path, 'city.geojson')
    logger.info(f"city_geojson_file_path: {city_geojson_file_path}")
    # Check for geojson files in current working directory
    cwd = os.getcwd()
    geojson_files = [f for f in os.listdir(cwd) if f.endswith('.geojson')]

    file_path = geojson_files[0] if geojson_files else None
    if file_path:
        print(file_path)
    else:
        logger.error("No geojson file found in the current directory.")
    # Call your function with the parsed arguments
    generate_EP_assets(file_path,args.multiplier, args.generate_DFenriched_geojson, args.filter_height_less_than, args.filter_height_greater_than, args.filter_area_less_than)