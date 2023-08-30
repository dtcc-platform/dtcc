import dtcc_model as model
import dtcc_io as io
import dtcc_data as data
import dtcc_wrangler as wrangler
import dtcc_builder as builder
import dtcc_viewer as viewer


# Collect __all__ from submodules
modules = [model, io, data, wrangler, builder, viewer]
__all__ = []
for module in modules:
    for name in module.__all__:
        globals()[name] = getattr(module, name)
    __all__ += module.__all__
