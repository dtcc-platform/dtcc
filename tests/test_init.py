import pytest
import dtcc  # Replace 'dtcc' with the actual package name if different

def test_logging_functions_exist():
    # Test that logging functions exist and are callable
    for func_name in ["debug", "info", "warning", "error", "critical"]:
        func = getattr(dtcc, func_name, None)
        assert func is not None, f"Expected {func_name} to be defined"
        assert callable(func), f"Expected {func_name} to be callable"

def test_all_list_populated():
    # Test that __all__ is not empty and contains at least the logging functions
    assert isinstance(dtcc.__all__, list), "__all__ should be a list"
    assert len(dtcc.__all__) > 0, "__all__ should not be empty"
    for name in ["debug", "info", "warning", "error", "critical"]:
        assert name in dtcc.__all__, f"{name} should be in __all__"

def test_imported_module_symbols():
    # Test that symbols imported from dtcc_core and dtcc_data are accessible
    for name in dtcc.__all__:
        attr = getattr(dtcc, name, None)
        assert attr is not None, f"Attribute {name} should be defined in the package"

def test_viewer_or_default_view():
    # Test handling of viewer availability
    if hasattr(dtcc, "is_graphical_available"):
        # If graphical functionality is available, then is_graphical_available should be callable and return a boolean.
        assert callable(dtcc.is_graphical_available), "is_graphical_available should be callable"
        result = dtcc.is_graphical_available()
        assert isinstance(result, bool), "is_graphical_available should return a boolean"
    else:
        # Otherwise, a default_view method should be defined for model classes.
        assert hasattr(dtcc, "default_view"), "default_view should be defined when dtcc_viewer is not available"
        assert callable(dtcc.default_view), "default_view should be callable"

def test_is_graphical_available_returns_boolean():
    # Test that graphic availability returns a boolean
    if hasattr(dtcc, "is_graphical_available"):
        result = dtcc.is_graphical_available()
        assert isinstance(result, bool), "is_graphical_available() must return a boolean"
