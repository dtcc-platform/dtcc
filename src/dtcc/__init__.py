# Option A: Expose all functions in the root namespace
from dtcc_io import load_pointcloud, load_footprints
from dtcc_builder import build_citymodel
from dtcc_viewer import view

__all__ = ['load_pointcloud', 'load_footprints', 'build_citymodel']

# Option B: Require explicit import of functions
# import dtcc_model as model
# import dtcc_io as io
# import dtcc_builder as builder
# import dtcc_viewer as viewer

# __all__ = ['model', 'io', 'builder', 'viewer']
