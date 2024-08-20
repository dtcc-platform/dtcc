# Import submodules
import dtcc_common as common
import dtcc_model as model
import dtcc_io as io
import dtcc_data as data
import dtcc_builder as builder
import dtcc_viewer as viewer


# Collect __all__ from submodules
modules = [common, model, io, data, builder, viewer]
__all__ = []
for module in modules:
    for name in module.__all__:
        globals()[name] = getattr(module, name)
    __all__ += module.__all__


# Local imports
from .logging import debug, info, warning, error, critical

__all__ += ["debug", "info", "warning", "error", "critical"]


# Import parameters from dtcc-builder. We should think about how to do this in a
# good way, perhaps we can have a common parameter set defined in dtcc-common
# and then all modules extend the parameter set with their own parameters.
from dtcc_builder import parameters

__all__.append("parameters")
