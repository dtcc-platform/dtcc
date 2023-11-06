# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License
#
# This demo illustrates how to build a city model from raw data,
# and viewing the resulting mesh model together with the pointcloud.
import dtcc

filename = "../data/helsingborg-residential-2022/pointcloud.las"
pc = dtcc.io.load_pointcloud(filename)
color_data = pc.points[:, 0]
pc.view(data=color_data)
