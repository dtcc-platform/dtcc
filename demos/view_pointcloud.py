# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License
#
# This demo illustrates how to build a city model from raw data,
# and viewing the resulting mesh model together with the pointcloud.

from dtcc import *

filename = '../data/dtcc-demo-data/helsingborg-residential-2022/pointcloud.las'
pc = load_pointcloud(filename)
color_data = pc.points[:,0]
pc.view(pc_data = color_data)