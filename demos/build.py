# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License
#
# This demo illustrates how to build a city model from raw data,
# equivalent to running the dtcc-build command-line utility.

from dtcc import *

# Set parameters
p = parameters.default()
p["data_directory"] = "data/helsingborg-residential-2022"
p["mesh_resolution"] = 20.0
p["domain_height"] = 75.0

# Build city model
build(p)
