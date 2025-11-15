# Import core submodules

from dtcc_core import common as common
from dtcc_core import model as model
from dtcc_core import io as io
from dtcc_core import builder as builder
import dtcc_data as data

modules = [common, model, io, builder, data,]
__all__ = []
for module in modules:
    for name in module.__all__:
        globals()[name] = getattr(module, name)
    __all__ += module.__all__

# Local imports
from .logging import debug, info, warning, error, critical
__all__ += ["debug", "info", "warning", "error", "critical"]

# Try to import dtcc_viewer
try:
    import dtcc_viewer as viewer
    import glfw

    def is_graphical_available():
        """Check if OpenGL via GLFW can be initialized."""
        if not glfw.init():
            return False
        glfw.terminate()
        return True

    if not is_graphical_available():
        raise ImportError("Failed to initialize GLFW. You are likely in a headless or non-graphical environment.")

    # Add dtcc_viewer to the list of modules if graphical environment is available
    modules.append(viewer)

except ImportError:
    # Define a default method to provide feedback when dtcc-viewer is not available
    def default_view(self,*args,**kwargs):
       warning(f"Cannot view object: {self.__class__.__name__}. The dtcc-viewer module is not installed or graphical rendering is not available. "
               "Please install dtcc-viewer using 'pip install dtcc-viewer'.")

    def _attach_default_view_to_model_classes():
        """Attach the default_view method to model classes that are subclasses of Model."""
        import inspect
        # Import Model locally within the function
        import dtcc_core.model
        from dtcc_core.model.model import Model as _Model

        dtcc_model_classes = [
            member for _, member in inspect.getmembers(dtcc_core.model)
            if inspect.isclass(member) and issubclass(member, _Model)
        ]

        for model_class in dtcc_model_classes:
            model_class.add_methods(default_view, "view")

    # Call the function to attach the default view method
    _attach_default_view_to_model_classes()


"""
Static imports for type checkers and IntelliSense.

These imports are wrapped in `if TYPE_CHECKING`, which is always `False` at
runtime. This means:
  - The imports below **never execute** when the package is imported normally,
    so they have **zero runtime cost** and do not introduce additional
    dependencies.
  - Static analyzers such as Pylance, Pyright, and mypy **do** evaluate them
    to understand which symbols are re-exported at the top level of the
    `dtcc` package.

In short: this block exists purely to give IDEs full autocomplete and
documentation for `dtcc.<symbol>` while keeping the runtime import logic
dynamic and lightweight.
"""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # These won't run at runtime, but Pylance will see them
    from dtcc_core.common import *      # noqa: F401, F403
    from dtcc_core.model import *       # noqa: F401, F403
    from dtcc_core.io import *          # noqa: F401, F403
    from dtcc_core.builder import *     # noqa: F401, F403
    from dtcc_data import *             # noqa: F401, F403
