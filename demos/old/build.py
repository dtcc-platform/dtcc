# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License
#
# This demo illustrates how to build a city model from raw data,
# equivalent to running the dtcc-build command-line utility.

from dtcc import *
from pathlib import Path

# Set parameters
p = parameters.default()
data_directory = Path(__file__).parent / ".." / "data/helsingborg-residential-2022"

p["data_directory"] = str(data_directory)
p["mesh_resolution"] = 5.0
p["domain_height"] = 75.0

# Build city model
build(p)
