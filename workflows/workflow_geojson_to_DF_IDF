import json
import logging
from math import ceil
from ladybug_geometry.geometry2d.pointvector import Point2D
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D
from dragonfly.model import Model
from dragonfly.building import Building
from dragonfly.story import Story
from dragonfly.room2d import Room2D
from dragonfly.windowparameter import SimpleWindowRatio, RepeatingWindowRatio
from honeybee_energy.lib.programtypes import office_program, ProgramType
import geopandas as gpd
# Constants
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


# 3. Modify the adjust_building_properties function to accept building heights
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
                    "{}_adjusted".format(room.identifier), face3d, floor_to_floor_height
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
            new_story = Story("{}_adjusted".format(story.identifier), new_room2d_set)
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
    new_model = Model("{}_adjusted".format(model.identifier), new_buildings)

    return new_model

# Main execution
if __name__ == '__main__':
    logging.info("Starting script execution...")

    geojson_file_path = PROJECT_DIRECTORY + 'city.geojson'
    logging.info(f"Loading data from {geojson_file_path}")
    data = load_geojson_data(geojson_file_path)
    building_heights = extract_building_heights(data)
    building_types = extract_building_types(data)
    logging.info("Creating Dragonfly model from GeoJSON...")
    model, _ = Model.from_geojson(geojson_file_path, point=Point2D(0, 0), units='Meters', all_polygons_to_buildings=True)

    logging.info("Adjusting building properties in the model...")
    adjusted_model = adjust_building_properties(model, building_heights,building_types)
    adjusted_model.to_dfjson('model', PROJECT_DIRECTORY)

    logging.info("Serializing the Dragonfly Model to Honeybee Models...")
    hb_models = adjusted_model.to_honeybee('Building', use_multiplier=False, tolerance=0.0001)

    logging.info("Converting Honeybee Models to IDF...")
    idfs = [hb_model.to.idf(hb_model) for hb_model in hb_models]

    logging.info("Script execution completed!")
