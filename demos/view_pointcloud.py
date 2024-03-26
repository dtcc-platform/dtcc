# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License
#
# This demo illustrates how to build a city model from raw data,
# and viewing the resulting mesh model together with the pointcloud.
import dtcc
from pathlib import Path

data_directory = Path(__file__).parent / ".." / "data/helsingborg-residential-2022"

filename = data_directory / "pointcloud.las"
pc = dtcc.io.load_pointcloud(filename)
color_data = pc.points[:, 2]
pc.view(data=color_data)
