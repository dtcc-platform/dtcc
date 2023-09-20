import json
import logging
import os
from math import ceil
import geopandas as gpd
from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D
from dragonfly.model import Model
from dragonfly.building import Building
from dragonfly.story import Story
from dragonfly.room2d import Room2D
from dragonfly.windowparameter import SimpleWindowRatio, RepeatingWindowRatio
from honeybee_energy.lib.programtypes import office_program, ProgramType
from honeybee_energy.run import to_openstudio_osw, to_gbxml_osw, run_osw,_face_to_gbxml_geo
from honeybee.model import Model as HBModel
from honeybee.config import folders as hb_folders
from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.writer import energyplus_idf_version
import xml.etree.ElementTree as ET
import re
# Constants
PROJECT_NAME = 'Uddevala'
FLOOR_TO_FLOOR_HEIGHT = 3
WINDOW_TO_WALL_RATIO = 0.1
WINDOW_HEIGHT = 1.6
WINDOW_SILL_HEIGHT = 0.7
WINDOW_TO_WINDOW_HORIZONTAL_SPACING = 3
ADD_DEFAULT_IDEAL_AIR = True
DEFAULT_PROGRAM = ProgramType('HighriseApartment')
PROJECT_DIRECTORY = 'data/uddevala/'
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

# Initialize the logger
logging.basicConfig(level=logging.INFO)

# 1. Load the GeoJSON Data
def load_geojson_data(filepath):
    """
    Load the GeoJSON data from the provided file path.

    :param filepath: Path to the geojson file.
    :return: Loaded GeoJSON data.
    """
    data = gpd.read_file(filepath)
    return data

# 2. Extract building heights from the GeoJSON data
def extract_building_heights(data):
    """
    Extract building heights from the GeoJSON data.

    :param data: Loaded GeoJSON data.
    :return: A list of building heights.
    """
    height_list = data["height"].to_list()
    return height_list

# 2.5 Extract building types from GeoJSON data
def extract_building_types(data):
    """
    Extract building types from the GeoJSON data.

    :param data: Loaded GeoJSON data.
    :return: A list of building types.
    """
    building_use_list = data["ANDAMAL_1T"].to_list()
    return building_use_list

def clean_room_id(room_id):
    # Remove '_Space' or '_Space_1' or '_1' from the end
    cleaned_id = re.sub(r'(_Space(_\d+)?)|(_\d+)$', '', room_id)
    return cleaned_id

def add_gbxml_space_boundaries(base_gbxml, honeybee_model, new_gbxml=None):
    """Add the SpaceBoundary and ShellGeometry to a base_gbxml of a Honeybee model.

    Note that these space boundary geometry definitions are optional within gbXML and
    are essentially a duplication of the required non-manifold geometry within a
    valid gbXML. The OpenStudio Forward Translator does not include such duplicated
    geometries (hence, the reason for this method). However, these closed-volume
    boundary geometries are used by certain interfaces and gbXML viewers.

    Args:
        base_gbxml: A file path to a gbXML file that has been exported from the
            OpenStudio Forward Translator.
        honeybee_model: The honeybee Model object that was used to create the
            exported base_gbxml.
        new_gbxml: Optional path to where the new gbXML will be written. If None,
            the original base_gbxml will be overwritten with a version that has
            the SpaceBoundary included within it.
    """
    # get a dictionary of rooms in the model
    logging.info('Preparing room_dict...')
    room_dict = {room.identifier: room for room in honeybee_model.rooms}

    # register all of the namespaces within the OpenStudio-exported XML
    ET.register_namespace('', 'http://www.gbxml.org/schema')
    ET.register_namespace('xhtml', 'http://www.w3.org/1999/xhtml')
    ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    ET.register_namespace('xsd', 'http://www.w3.org/2001/XMLSchema')
    logging.info('Parsing gbXML...')
    # parse the XML and get the building definition
    tree = ET.parse(base_gbxml)
    root = tree.getroot()
    gbxml_header = r'{http://www.gbxml.org/schema}'
    building = root[0][1]

    # loop through surfaces in the gbXML so that we know the name of the interior ones
    logging.info('Getting surface names...')
    surface_set = set()
    for room_element in root[0].findall(gbxml_header + 'Surface'):
        surface_set.add(room_element.get('id'))

    # loop through the rooms in the XML and add them as space boundaries to the room
    logging.info('Parsing rooms with Spaces...')
    for room_element in building.findall(gbxml_header + 'Space'):
        room_id = room_element.get('zoneIdRef')
        if room_id:
            room_id = room_element.get('id')
            shell_element = ET.Element('ShellGeometry')
            shell_element.set('id', '{}Shell'.format(room_id))
            shell_geo_element = ET.SubElement(shell_element, 'ClosedShell')
            # Remove _Space* from the end of the room_id            
            hb_room = room_dict[clean_room_id(room_id)]  # remove '_Space' from the end
            for face in hb_room:
                face_xml, face_geo_xml = _face_to_gbxml_geo(face, surface_set)
                if face_xml is not None:
                    room_element.append(face_xml)
                    shell_geo_element.append(face_geo_xml)
            room_element.append(shell_element)
    logging.info('Writing out the new XML...')
    # write out the new XML
    new_xml = base_gbxml if new_gbxml is None else new_gbxml
    tree.write(new_xml, xml_declaration=True)
    return new_xml

def adjust_building_properties(model, building_heights, building_type, floor_to_floor_height=FLOOR_TO_FLOOR_HEIGHT):
    """
    Adjust properties of buildings in the model using provided building heights.

    :param model: Dragonfly model.
    :param building_heights: List of building heights.
    :param floor_to_floor_height: Height for each floor. Default is 3.
    :return: New Dragonfly model with adjusted buildings.
    """
    new_buildings = []

    for index, building in enumerate(model.buildings):
        ground_height = building_heights[index]  # get the building height from the list
        new_story_set = []

        for story in building._unique_stories:
            new_room2d_set = []

            for room in story.room_2ds:
                # Adjust the coordinates for ground height
                adjusted_coords = [Point3D(pt.x, pt.y, ground_height) for pt in room.floor_geometry.boundary]
                face3d = Face3D(adjusted_coords)

                # Create a new Room2D
                new_room = Room2D(
                    room.identifier, face3d, floor_to_floor_height
                )
                # assign energy properties
                #TODO Assign a vintage to the buildings based on year of construction
                #TODO Assign a climate zone to the building based on location
                building_program = BUILDING_PROGRAM_DICT.get(building_type[index])
                program = ProgramType(building_program)
                new_room.properties.energy.program_type = program
                if ADD_DEFAULT_IDEAL_AIR:
                    new_room.properties.energy.add_default_ideal_air()
                new_room2d_set.append(new_room)

            # Create a new Story with adjusted Room2Ds
            new_story = Story(story.identifier, new_room2d_set)
            new_story.solve_room_2d_adjacency(0.01)
            
            
            # Set window parameters for the new story
            new_story.set_outdoor_window_parameters(RepeatingWindowRatio(
                WINDOW_TO_WALL_RATIO,
                WINDOW_HEIGHT,
                WINDOW_SILL_HEIGHT,
                WINDOW_TO_WINDOW_HORIZONTAL_SPACING
            ))
            # Calculate and set the multiplier for the new story
            multiplier = ceil(ground_height / floor_to_floor_height)
            new_story.multiplier = multiplier

            new_story_set.append(new_story)

        # Create a new Building with adjusted stories
        new_building = Building("{}_{}".format(building.identifier,index), new_story_set)
        new_buildings.append(new_building)

    # Create a new Dragonfly Model with adjusted buildings
    new_model = Model(model.identifier, new_buildings)

    return new_model


_logger = logging.getLogger(__name__)

def model_to_hb_models(model, multiplier=False, no_plenum=True, no_ceil_adjacency=True):
    """Translate a Model DFJSON to a Honeybee Model."""

    model.convert_to_units('Meters')

    # convert Dragonfly Model to Honeybee
    add_plenum = not no_plenum
    ceil_adjacency = not no_ceil_adjacency
    hb_models = model.to_honeybee(
        object_per_model='District', use_multiplier=multiplier,
        add_plenum=add_plenum, solve_ceiling_adjacencies=ceil_adjacency)
    return hb_models

def models_to_idf(hb_models, additional_str = '', compact_schedules = True, 
                  hvac_to_ideal_air = True, output_file_path= None):
    """Translate a Honeybee model to an IDF file."""
    
    hb_model = hb_models[0]

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
        _logger.exception('Model translation failed.\n{}'.format(e))
        raise e

    return output_file_path

def models_to_gbxml(hb_models,no_plenum=True,
                   no_ceil_adjacency=True, osw_folder=None, output_file_path=None):
    out_directory = PROJECT_DIRECTORY  # assuming you want to use the default folder
    hb_model = hb_models[0]
    logging.info('Writing gbXML file to: {}'.format(out_directory))
    # create the dictionary of the HBJSON for input to OpenStudio CLI
    for room in hb_model.rooms:
        room.remove_colinear_vertices_envelope(0.01, delete_degenerate=True)
    model_dict = hb_model.to_dict(triangulate_sub_faces=True)
    hb_model.properties.energy.add_autocal_properties_to_dict(model_dict)
    hb_model_json = os.path.abspath(os.path.join(out_directory, 'city.hbjson'))
    with open(hb_model_json, 'w') as fp:
        json.dump(model_dict, fp)
    logging.info('Wrote HBJSON file to: {}'.format(hb_model_json))
    # Write the osw file and translate the model to gbXML
    output_file_path = os.path.abspath(os.path.join(out_directory, 'city.gbxml'))
    osw = to_gbxml_osw(hb_model_json, output_file_path, PROJECT_DIRECTORY)
    logging.info('Wrote OSW file to: {}'.format(osw))
    try:
        logging.info('Running OpenStudio CLI to translate to gbXML...')
        _, idf = run_osw(osw, silent=False)

        if idf is not None and os.path.isfile(idf):
            hb_model = HBModel.from_hbjson(hb_model_json)
            logging.info('Adding space boundaries to gbXML file: {}'.format(output_file_path))
            add_gbxml_space_boundaries(output_file_path, hb_model)
            logging.info('Added space boundaries to gbXML file: {}'.format(output_file_path))
            #if output_file_path is not None:
                #with open(output_file_path) as json_file:
                    #print(json_file.read())
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        raise e

    return output_file_path

# Main execution
def generate_EP_assets(geojson_file_path):
    logging.info("Starting script execution...")

    geojson_file_path = PROJECT_DIRECTORY + 'city.geojson'
    logging.info(f"Loading data from {geojson_file_path}")
    data = load_geojson_data(geojson_file_path)
    building_heights = extract_building_heights(data)
    building_types = extract_building_types(data)
    logging.info("Creating Dragonfly model from GeoJSON...")

    model, _ = Model.from_geojson(geojson_file_path, point=Point2D(0, 0), units='Meters', all_polygons_to_buildings=True)
    #model.identifier = PROJECT_NAME
    logging.info("Adjusting building properties in the model...")
    adjusted_model = adjust_building_properties(model, building_heights, building_types)
    adjusted_model.to_dfjson('city', PROJECT_DIRECTORY)

    logging.info("Serializing the Dragonfly Model to Honeybee Models...")
    hb_models = model_to_hb_models(adjusted_model, multiplier = False, no_plenum=True, no_ceil_adjacency=True)

    logging.info("Converting Honeybee Models to IDF...")
    #idfs = [hb_model.to.idf(hb_model) for hb_model in hb_models]
    models_to_idf(hb_models, output_file_path = PROJECT_DIRECTORY + 'city.idf')

    #TODO Replicate CLI commands for running the IDF file
    logging.info("Converting Honeybee Models to GBXML...")
    models_to_gbxml(hb_models, output_file_path=PROJECT_DIRECTORY + 'city.gbxml')

    logging.info("Script execution completed!")

if __name__ == '__main__':
    generate_EP_assets(PROJECT_DIRECTORY + 'city.geojson')
