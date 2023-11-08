#!/usr/bin/env python3

import numpy as np
import pandas as pd
import math
import datetime
import matplotlib.pyplot as plt
import argparse

from windrose import WindroseAxes
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom



class Windrose:
    """Create a windrose from wind speed and direction data.
    
    This class takes wind speed and direction data, creates a windrose,
    and provides methods to save the windrose as an image or as XML data.
    
    Parameters
    ----------
    data : pandas.DataFrame
        The input data containing wind speed and direction.
    parameters : dict, optional
        Custom parameters for windrose generation, by default None.
    create : bool, optional
        Indicates whether to create the windrose upon initialization, by default True.
    
    Attributes
    ----------
    raw_data : pandas.DataFrame
        The raw input data.
    date : list
        List of dates from the input data.
    time : list
        List of times from the input data.
    time_objects : list
        List of datetime objects derived from date and time.
    wind_direction : list
        List of wind directions.
    direction_quality : list
        List of direction quality values.
    wind_speed : list
        List of wind speeds.
    speed_quality : list
        List of wind speed quality values.
    
    Methods
    -------
    save_figure(filename, format='png')
        Save the windrose as an image.
    to_xml(filename)
        Save the windrose data as an XML file.
    
    Examples
    --------
    >>> data = pd.read_csv('wind_data.csv')
    >>> wr = Windrose(data)
    >>> wr.save_figure('windrose.png')
    >>> wr.to_xml('windrose.xml')
    """
    _parameters = {
        "exlude_defects": None,
        "angle_bin_num": None,
        "velocity_bin_num": None,
        "velocity_min": None,
        "velocity_max": None,
        "velocity_bins": None,
        "define_velocity_bins": None,
        "height": None
    }
    raw_data: pd.DataFrame
    
    date: list
    time: list
    time_objects: list
    
    wind_direction: list = []
    direction_quality: list
    
    wind_speed: list 
    speed_quality: list
    
    _windrose_norm : np.ndarray
    _bin_degrees = []
    _bin_vel = []
    
    

    def __init__(self, data: pd.DataFrame, parameters: dict = None, create: bool = True) -> None:
        """Initialize the Windrose object.
        
        Parameters
        ----------
        data : pandas.DataFrame
            The input data containing wind speed and direction.
        parameters : dict, optional
            Custom parameters for windrose generation, by default None.
        create : bool, optional
            Indicates whether to create the windrose upon initialization, by default True.
        """
        if parameters is None:
            self._parameters = self.default_parameters()
        else:
            self._parameters = parameters

        
        self.raw_data = data 
        if "Datum" not in data.columns:
            print("Data (pd.Dataframe) does not contain date information (Datum)")
            return None 
        self.date = data["Datum"]
        if "Tid (UTC)" not in data.columns:
            print("Data (pd.Dataframe) does not contain time information (Tid \(UTC\)")
            return None 
        self.time = data["Tid (UTC)"]
        if "Vindriktning" not in data.columns:
            print("Data (pd.Dataframe) does not contain wind direction information (Vindriktning)")
            return None
        self.wind_direction = data["Vindriktning"].astype(float)
        self.direction_quality = data["Kvalitet"]  # G for good and Y for defective
        if "Vindhastighet" not in data.columns:
            print("Data (pd.Dataframe) does not contain wind speed information (Vindriktning)")
            return None
        self.wind_speed = data["Vindhastighet"].astype(float)
        self.speed_quality = data["Kvalitet.1"]  # G for good and Y for defective
        
        num_obs = 0

        timeObj = np.zeros(len(self.time), dtype=datetime.datetime)
        for d, t in zip(self.date, self.time):
            timeStr = d + " " + t
            timeObj[num_obs] = datetime.datetime.strptime(timeStr, "%Y-%m-%d %H:%M:%S")
            num_obs = num_obs + 1
        self.time_objects = timeObj
        
        if create: 
            self.create()
            
    def default_parameters(self):
        """Get the default parameters for windrose generation.
        
        Returns
        -------
        dict
            A dictionary of default parameters.
        """
        default_parameters = {}

        default_parameters["exlude_defects"] = False
        default_parameters["angle_bin_num"] = 8
        default_parameters["velocity_bin_num"] = 8
        default_parameters["velocity_min"] = 0.0
        default_parameters["velocity_max"] = 100.0
        default_parameters["velocity_bins"] = [
            0.0,
            0.5,
            2.0,
            4.0,
            6.0,
            8.0,
            10.0,
            12.0,
            14.0,
            16.0,
            18.0,
            100.0,
        ]
        default_parameters["define_velocity_bins"] = True
        default_parameters["height"] = 10.0
        return default_parameters.copy()

    def get_parameters(self):
        """Get the current parameters for windrose generation.
        
        Returns
        -------
        dict
            A dictionary of current parameters.
        """
        return self._parameters.copy()

    def set_parameter(self, key: str, value):
        """Set a parameter for windrose generation.
        
        Parameters
        ----------
        key : str
            The name of the parameter.
        value
            The value to set for the parameter.
        """
        if not isinstance(key, str):
            print("Invalid key. Key must be a string.")
            return
        try:
            # Attempt to access a key that may or may not exist
            self._parameters[key] = value
        except KeyError as e:
            # Handle the KeyError here
            print(f"KeyError: {e} - The key {key} does not exist in the dictionary.")
        else:
            # Code to execute if the key exists
            print(f"The value is: {value}")

    def create(self):
        """Create the windrose from the input data."""
        parameters = self.get_parameters()

        # Create the binning
        angle_bin_num = parameters["angle_bin_num"]
        bin_size = 360 / angle_bin_num
        bin_degrees = np.arange(0, 360 + bin_size, bin_size)

        # binVelSize=(max(speed)-min(speed))/(opts.nVel-1)
        velocity_bin_num = parameters["velocity_bin_num"]

        if parameters["define_velocity_bins"]:
            binVel = np.array(parameters["velocity_bins"], dtype=float)
            velocity_bin_num = len(binVel) - 1
        # binVel=np.arange(min(speed)-max(binVelSize,0),max(speed)+binVelSize,binVelSize)
        windrose = np.zeros((angle_bin_num, velocity_bin_num))

        print(binVel)
        print(bin_degrees)

        # Put all the data in the bins
        k = 0
        totalTime = 0
        count = 0
        for d, qD, s, qS, t in zip(
            self.wind_direction, self.direction_quality, self.wind_speed, self.speed_quality, self.time_objects):
            if not (
                parameters["exlude_defects"] and (qD == "Y" or qS == "Y")
            ):  # TODO: if excludeDefect is used, the time needs to adjusted
                i = 0
                success = False
                while i < angle_bin_num:
                    if math.isclose(d, 0):
                        d = 1  # Hack to assign 0 also to the smallest bin
                    if d <= bin_degrees[i + 1] and d > bin_degrees[i]:
                        j = 0
                        while j < velocity_bin_num:
                            if (s <= binVel[j + 1] and s > binVel[j]) or (
                                math.isclose(s, binVel[j + 1])
                            ):
                                success = True
                                # print(s)
                                if t.hour == 0 or k == 0:
                                    windrose[i, j] = windrose[i, j] + (
                                        self.time_objects[k + 1].hour - t.hour
                                    )  # Assuming full hours
                                    totalTime = totalTime + (self.time_objects[k + 1].hour - t.hour)
                                elif k == len(self.wind_direction) and t.hour == 0:
                                    pass  # Do nothing
                                else:
                                    windrose[i, j] = windrose[i, j] + (
                                        t.hour - self.time_objects[k - 1].hour
                                    )  # Assuming full hours
                                    totalTime = totalTime + (t.hour - self.time_objects[k - 1].hour)
                            j = j + 1
                    i = i + 1
            if success:
                count = count + 1
            k = k + 1
        print("Successfull findings: ", count)

        # Calculate the frequency
        print("Total time:", totalTime)
        print("Windrose:", windrose)
        print("Total time:", sum(sum(windrose)))
        print("k:", k)
        windrose = windrose / totalTime

        self._bin_degrees = bin_degrees
        self._bin_vel = binVel
        self._windrose_norm = windrose
        
        
        
    def save_figure(self, filename: str, format: str = None):
        """Save the windrose figure as an image.
        
        Parameters
        ----------
        filename : str
            The name of the output image file.
        format : str, optional
            The format of the output image (e.g., 'png', 'jpg'), by default None.
        """
        if format is None:
            format = "png"
        
        f = plt.figure
        ax = WindroseAxes.from_ax()
        ax.bar(self.wind_direction, self.wind_speed, nsector=12)
        ax.legend()
        plt.savefig(filename, format= format)   
        
        
    def to_xml(self, filename: str):
        """Save the windrose data as an XML file.
        
        Parameters
        ----------
        filename : str
            The name of the output XML file.
        """
        
        # Create the root element
        root = ET.Element("windrose_data")

        # Create height element
        height = ET.SubElement(root, "height")
        height.set("value", str(self._parameters["height"]))

        roughness_val = 0.5
        # Create reference_roughness element
        reference_roughness = ET.SubElement(root, "reference_roughness")
        reference_roughness.set("value", str(roughness_val))

        # Create roughness_list element
        roughness_list = ET.SubElement(root, "roughness_list")

        # Create roughness elements within roughness_list
        for _ in range(self._parameters["angle_bin_num"]):
            roughness = ET.SubElement(roughness_list, "roughness")
            roughness.set("value", str(roughness_val))

        # Create angle_list element
        angle_list = ET.SubElement(root, "angle_list")

        # Create angle elements within angle_list
        for angle_value in self._bin_degrees:
            angle = ET.SubElement(angle_list, "angle")
            angle.set("value", str(angle_value))

        # Create velocity_list element
        velocity_list = ET.SubElement(root, "velocity_list")

        # Create velocity elements within velocity_list
        for velocity_value in self._bin_vel:
            velocity = ET.SubElement(velocity_list, "velocity")
            velocity.set("x", str(velocity_value))
            velocity.set("y", "0.0")
            velocity.set("z", "0.0")

        # Create frequency element
        frequency = ET.SubElement(root, "frequency")

        # Create angle elements within frequency
        for angle_values in self._windrose_norm:
            angle_element = ET.SubElement(frequency, "angle")
            for vel_value in angle_values:
                vel = ET.SubElement(angle_element, "vel")
                vel.set("value", str(vel_value))

        # Create an XML tree from the root element
        xml_string = ET.tostring(root, encoding="utf-8").decode("utf-8")
        dom = minidom.parseString(xml_string)
        formatted_xml = dom.toprettyxml(indent="    ")  # You can specify the desired indentation here

        # Write the XML to a file
        with open(filename, "w") as f: 
            f.write(formatted_xml)   
            
        
def main(args):
    """ Script to generate the windrose from measruements of wind speeds according to the 
    SMHI format:
    Datum	    Tid (UTC)	Vindriktning	Kvalitet	Vindhastighet	Kvalitet
    1951-01-01	00:00:00	100	                G	        3.0	            G
    1951-01-01	03:00:00	110	                G	        2.0	            G
    1951-01-01	06:00:00	70	                G	        2.0	            G

    """
    data = pd.read_csv(args.filename, delimiter=";", usecols=(0, 1, 2, 3, 4, 5))
    print(data)

    wndrs = Windrose(data)
    parameters = wndrs._parameters
    wndrs.save_figure("Wiiiiindrose.png")
    wndrs.to_xml("TESTtest.xml")
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="CreateWindrose",
        description="Creates windrose statistics from SMHI data file in xml format for IBOFlow and plot in addition",
        epilog="No warranty",
    )
    parser.add_argument("filename")  # positional argument
    parser.add_argument("-nDeg", "--numberDegrees")  # option that takes a value
    args = parser.parse_args()

    main(args)
