import dtcc_model
import dtcc_io

# Collect __all__ from submodules
modules = [dtcc_model, dtcc_io]
__all__ = []
for module in modules:
    for name in module.__all__:
        globals()[name] = getattr(module, name)
    __all__ += module.__all__
