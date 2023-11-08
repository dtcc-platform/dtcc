#!/usr/bin/env python3

# Script fot downloading Meteorological observations from 
# the Swedish Meteorological and Hydrological Institute (SMHI)

import requests
import json
from io import StringIO
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points

import pandas as pd
from enum import Enum


class SMHIMetObsAPI:
    """
    A class for accessing meteorological observations from the Swedish Meteorological and Hydrological Institute (SMHI) API.

    Attributes:
        _base_url (str): The base URL for the SMHI API.
        _latest_version (str): The latest version of the API.
        _available_periods (set): Available time periods for data retrieval.
        _available_station_sets (set): Available station sets.
        _available_stations (dict): Available weather stations.

    Methods:
        __init__(self, version="1.0", station_set=None):
            Initializes the SMHIMetObsAPI object.

        get_available_stations(self, parameter=None):
            Retrieves available weather stations for a given parameter.

        get_closest_station(self, lon, lat):
            Finds the closest weather station to a specified longitude and latitude.

        _request_by_station(self, station, parameter, period):
            Makes an API request for data by station, parameter, and period.

        request(self, parameter=None, station=None, latitude=None, longitude=None, period=None):
            Makes a request to the SMHI API for meteorological data.
    """
    _base_url: str = "https://opendata-download-metobs.smhi.se/api"

    _latest_version = "1.0"
  
    _available_periods = {
        "latest-hour",
        "latest-day",
        "latest-months",
        "corrected-archive"
    }

    _available_station_sets = {"all", "core", "additional"}

    _available_stations = {}

    class _AvailableParameter(Enum):
        """
        An enumeration of available meteorological parameters.
        """
        
        WIND_SPEED = 21  # max, 1 time per hour
        DEW_POINT_TEMPERATURE = 39  # instantaneous value, 1 time per hour
        GLOBAL_IRRADIANCE = 11  # average 1 hour, 1 time per hour
        AIR_TEMPERATURE_MONTHLY = 22  # average, 1 time per month
        AIR_TEMPERATURE_MIN_DAILY = 26  # minimum, 2 times per day, at 06 and 18
        AIR_TEMPERATURE_MAX_DAILY = 27  # maximum, 2 times per day, at 06 and 18
        AIR_TEMPERATURE_MIN_DAILY_2 = 19  # minimum, 1 time per day
        AIR_TEMPERATURE_INSTANT = 1  # instantaneous value, 1 time per hour
        AIR_TEMPERATURE_DAILY = 2  # average 1 day, 1 time per day, at 00
        AIR_TEMPERATURE_MAX_DAILY_2 = 20  # maximum, 1 time per day
        REDUCED_SEA_LEVEL_PRESSURE = (
            9  # at sea level, instantaneous value, 1 time per hour
        )
        LONGWAVE_IRRADIANCE = 24  # Longwave radiation, average 1 hour, every hour
        SOIL_CONDITION = 40  # instantaneous value, 1 time per day, at 06
        MAX_MEAN_WIND_SPEED = (
            25  # maximum of mean 10-minute average, under 3 hours, 1 time per hour
        )
        CLOUD_BASE_LOWEST = (
            28  # lowest cloud layer, instantaneous value, 1 time per hour
        )
        CLOUD_BASE_SECOND = (
            30  # second cloud layer, instantaneous value, 1 time per hour
        )
        CLOUD_BASE_THIRD = 32  # third cloud layer, instantaneous value, 1 time per hour
        CLOUD_BASE_FOURTH = (
            34  # fourth cloud layer, instantaneous value, 1 time per hour
        )
        CLOUD_BASE_LOWEST_2 = (
            36  # lowest cloud base, instantaneous value, 1 time per hour
        )
        CLOUD_BASE_LOWEST_3 = (
            37  # lowest cloud base, minimum under 15 minutes, 1 time per hour
        )
        CLOUD_COVER_LOWEST = (
            29  # lowest cloud layer, instantaneous value, 1 time per hour
        )
        CLOUD_COVER_SECOND = (
            31  # second cloud layer, instantaneous value, 1 time per hour
        )
        CLOUD_COVER_THIRD = (
            33  # third cloud layer, instantaneous value, 1 time per hour
        )
        CLOUD_COVER_FOURTH = (
            35  # fourth cloud layer, instantaneous value, 1 time per hour
        )
        PRECIPITATION_TWICE_DAILY = 17  # 2 times per day, at 06 and 18
        PRECIPITATION_ONCE_DAILY = 18  # 1 time per day, at 18
        PRECIPITATION_INTENSITY = 15  # maximum under 15 minutes, 4 times per hour
        PRECIPITATION_INTENSITY_MAX = (
            38  # maximum of mean under 15 minutes, 4 times per hour
        )
        PRECIPITATION_AMOUNT_MONTHLY = 23  # sum, 1 time per month
        PRECIPITATION_AMOUNT_15_MIN = 14  # sum 15 minutes, 4 times per hour
        PRECIPITATION_AMOUNT_DAILY = 5  # sum 1 day, 1 time per day, at 06
        PRECIPITATION_AMOUNT_HOURLY = 7  # sum 1 hour, 1 time per hour
        RELATIVE_HUMIDITY = 6  # instantaneous value, 1 time per hour
        CURRENT_WEATHER = 13  # instantaneous value, 1 time per hour, or 8 times per day
        VISIBILITY = 12  # instantaneous value, 1 time per hour
        SNOW_DEPTH = 8  # instantaneous value, 1 time per day, at 06
        SUNSHINE_DURATION = 10  # sum 1 hour, 1 time per hour
        TOTAL_CLOUD_COVER = 16  # instantaneous value, 1 time per hour
        WIND_SPEED_10_MIN_AVERAGE = 4  # mean 10-minute average, 1 time per hour
        WIND_DIRECTION_10_MIN_AVERAGE = 3  # mean 10-minute average, 1 time per hour

    
    version: str = _latest_version
    parameter: int
    station_set: str = "all"
    station: int 
    period: str

    def __init__(self, version: str = "1.0", station_set: str = None):
        """
        Initializes the SMHIMetObsAPI object.

        Args:
            version (str): The desired API version (default is "1.0").
            station_set (str): The desired station set (default is "all").
        """
        
        # Configuring API Version to use
        version = str(version)
        version_num = float(version)
        latest_version_num = float(self._latest_version)
        if version_num > latest_version_num:
            print("Not a valid API version")
            print(f"Using latest version: {self._latest_version}")
        elif version_num < latest_version_num:
            version_url = self._base_url + "/version/" + str(version)
            version_check = requests.get(version_url)
            if version_check.status_code == 200:
                self.version = version
            else:
                print("Not a valid API version")
                print(f"Using latest version: {self._latest_version}")
        
        # Configuring measuring Station Set to use:
        station_set = str(station_set)
        if station_set in self._available_station_sets:
            self.station_set = station_set
        else:
            print("Not a valid Station Set")
            print("Using station Set: \"all\" " )
        
        self._available_stations = self.get_available_stations(parameter = 1)

    
    def get_available_stations(self, parameter: int = None):
        """
        Retrieves available weather stations for a given parameter.

        Args:
            parameter (int): The parameter for which to retrieve stations.

        Returns:
            dict: A dictionary of available weather stations with their IDs and coordinates.
        """
        if any(parameter == item.value for item in self._AvailableParameter):
            self.parameter = parameter
        if any(parameter == item for item in self._AvailableParameter):
            self.parameter = parameter.value
        stations_url = "https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/" 
        url = stations_url + str(self.parameter) +"?measuringStations=" + self.station_set
        stations = requests.get(url)
        status = stations.status_code
        stations_dict = {}
        
        if(status == 200):
            for line in stations.iter_lines():
                
                if line:
                    text_line = str(line)
                            
                    if(text_line.find("<id>"))!= -1:
                        segs = text_line.split('.')
                        some_seg = segs[3]
                        segs = some_seg.split('/')
                        id = segs[-1]
                        
                    if(text_line.find("Latitud: ")) != -1:
                        segs = text_line.split(':')
                        lat_segs = segs[1].split(' ')
                        lat_num = float(lat_segs[1])

                        lon_segs = segs[2].split(' ')
                        lon_num = float(lon_segs[1])

                        types = ['Latitude', 'Longitude']
                        pos_dict = dict.fromkeys([t for t in types])
                        pos_dict['Latitude'] = lat_num
                        pos_dict['Longitude'] = lon_num
                        stations_dict[id] = pos_dict

            return stations_dict

    def get_closest_station(self, lon, lat):
        """
        Finds the closest weather station to a specified longitude and latitude.

        Args:
            lon (float): The longitude of the location.
            lat (float): The latitude of the location.

        Returns:
            int: The ID of the closest weather station.
        """
        closest_station_id = None
        min_distance = float('inf')
        input_point = (lon, lat)      
        for station_id, station in self._available_stations.items():
            station_point = (station['Longitude'], station['Latitude'])
            distance = squared_distance(input_point, station_point)
            if distance < min_distance:
                min_distance = distance
                closest_station_id = station_id

        return closest_station_id

    #/parameter/25/station/159880/period/corrected-archive/data.csv"
    def _request_by_station(self,station, parameter, period):
        """
        Makes an API request for data by station, parameter, and period.

        Args:
            station (int): The ID of the weather station.
            parameter (int): The parameter for which to request data.
            period (str): The time period for data retrieval.

        Returns:
            str: The response text from the API request.
        """
        available_stations = self.get_available_stations(parameter)
        if str(station) not in available_stations: 
            print("Given Station not in available stations")
        
        url = (self._base_url
            + "/version/" + self.version
            + "/parameter/" + str(parameter)
            + "/station/"  +  str(station)
            + "/period/" + period
            + "/data.csv"
        )

        print(url)

        response = requests.get(url)
        status = response.status_code
        print(f' Status code: {status}')
       
        if(status == 200): 
            return response.text
        elif(status == 404):
            print("SMHI Open Data API Docs HTTP code 404:")
            print("The request points to a resource that do not exist." +
            "This might happen if you query for a station that do" +
            "not produce data for a specific parameter or you are" +
            "using a deprecated version of the API that has been" +
            "removed. It might also be the case that the specified" +
            "station do not have any data for the latest hour.")
        elif (status == 500):
            print("SMHI Open Data API Docs HTTP code 500:")    
            print("Something went wrong internally in the system. This" +
                "might be fixed after a while so try again later on.")    

        return None

    def request(self, parameter = None, 
                station = None,
                latitude: float = None,
                longitude: float = None,
                period = None):
        """
        Makes a request to the SMHI API for meteorological data.

        Args:
            parameter (int): The parameter for which to request data.
            station (int): The ID of the weather station.
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.
            period (str): The time period for data retrieval.

        Returns:
            pandas.DataFrame: A DataFrame containing the requested meteorological data.
        """
        if any(parameter == item.value for item in self._AvailableParameter):
            self.parameter = parameter
        elif any(parameter == item for item in self._AvailableParameter):
            self.parameter = parameter.value
        else: 
            print("Parameter has to be one the available measurements")
            return None
        
        if period not in self._available_periods:
            print("Period has to be one of the available periods:")
            print(self._available_periods)
            return None
        
        if station == None:
            if ((latitude != None) and (longitude != None)):
                longitude,latitude = check_geo_data(longitude,latitude)
                station = self.get_closest_station(longitude,latitude)
                print(f'Using station closest to point: {station}')
            else: 
                print("Either the station parameter or lat,lon must have a value")
                return None
            
        # Format Response text from API call 
        data = self._request_by_station(station=station, parameter= self.parameter, period=period)
        header_lines_to_remove = find_csv_header(data)
        
        pandas_data = pd.read_csv(StringIO(data), sep=";", skiprows= header_lines_to_remove)
        pandas_data = pandas_data.iloc[:,:4]

        return pandas_data


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ UTILITIES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def find_csv_header(text):
    """
    Finds the line number of the CSV header in the given text.

    Args:
        text (str): The text containing CSV data.

    Returns:
        int: The line number of the CSV header.
    """
    lines = text.splitlines() 
    for line_num, line in enumerate(lines):
        if "Datum;" in line:
            if line_num > 0:
                return line_num-1
            else:
                return 0 
            

def remove_first_n_lines(text, n):
    """
    Finds the line number of the CSV header in the given text.

    Args:
        text (str): The text containing CSV data.

    Returns:
        int: The line number of the CSV header.
    """
    
    # Split the string into lines
    lines = text.splitlines()

    # Check if there are at least n lines
    if len(lines) >= n:
        # Slice the list of lines to exclude the first n lines
        lines = lines[n:]

        # Join the remaining lines back into a string
        result = "\n".join(lines)

        return result
    else:
        # If there are fewer than n lines, return an empty string
        return ""

def check_geo_data(lon, lat):
    """
    Checks if the provided longitude and latitude are within the SMHI data domain.

    Args:
        lon (float): The longitude of the location.
        lat (float): The latitude of the location.

    Returns:
        float: Adjusted longitude (if outside domain).
        float: Adjusted latitude (if outside domain).
    
    Notes:
        Data from the SMHI north of Europe databased is limited to:
            1. Records from 2014 and later.
            2. The domain is limited to: Koordinater för området ges av hörnen:
            - South west corner: `Lon 2.0`,  `Lat 52.4` 
            - North west corner: `Lon 9.5`,  `Lat 71.5`, 
            - North east corner: `Lon 39.7`, `Lat 71.2`
            - South east corner: `Lon 27.8`, `Lat 52.3` 
    """
    test_pt = Point(lon, lat)
    geo_coords = [(2.0, 52.4), (9.5, 71.5), (39.7, 71.2), (27.8, 52.3)]
    geo_polygon = Polygon(geo_coords)

    if(not geo_polygon.contains(test_pt)):
        p1, p2 = nearest_points(geo_polygon, test_pt)
        lon = p1.x
        lat = p1.y
        print("Warning: Location is outside of weather data domain" +
              "The closest location to the domain is locaded at, " +
              "(lon: " + str(lon) + ", lat: " + str(lat) + ")" )

    return lon, lat

def squared_distance(point1, point2):
    """
    Calculates the squared distance between two points.

    Args:
        point1 (tuple): The coordinates of the first point (lon, lat).
        point2 (tuple): The coordinates of the second point (lon, lat).

    Returns:
        float: The squared distance between the two points.
    """
    return (point1[0] - point2[0])**2 + (point1[1] - point2[1])**2


def main():
    """
    The main function that demonstrates the usage of the SMHIMetObsAPI class.

    Usage:
        - Initializes the API object.
        - Retrieves available weather stations.
        - Requests meteorological data for wind speed and wind direction.
        - Merges the data and saves it to a CSV file.
    """
    print("SMHI Meteorological Observations API")

    # url = "https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/25/station/159880/period/corrected-archive/json"
    # url = "https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/25/station/159880/period/corrected-archive/data.csv"
    
    Metobs = SMHIMetObsAPI(version="0.9", station_set="all")
    stations = Metobs.get_available_stations(parameter=25)
    wind_speed_data = Metobs.request(parameter = 3, station= 188790, period="corrected-archive")
    wind_direction_data = Metobs.request(parameter = 4, station= 188790, period="corrected-archive")
    wind_direction_data.rename(columns={'Kvalitet': 'Kvalitet.1'}, inplace=True)
    #data = Metobs.request(parameter = 25, longitude=18.8163, latitude=68.3538 , period="corrected-archive")
    data = pd.merge(wind_speed_data, wind_direction_data, on = ['Datum', 'Tid (UTC)'])
    print(data)
    data.to_csv("/home/auth-georspai/dtcc/workflows/iboflow/test_windrose.csv",sep=";" ,index = False)

if __name__ == "__main__":
    main()
