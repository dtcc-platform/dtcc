import os

# General information about the project
project = "DTCC Platform"
author = "Digital Twin Cities Centre"
copyright = "Digital Twin Cities Centre (2025)"
version = "develop"

# Determine whether to skip API docs generation.
skip_api = os.environ.get("NO_API", "0") == "1"

# Sphinx configuration
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "sphinx_immaterial",
]

if skip_api:
    print("Skipping building API docs")
    exclude_patterns = ["_api"]
else:
    print("Building API docs enabled")
    extensions.append("sphinx_immaterial.apidoc.python.apigen")
    python_apigen_modules = {"dtcc": "_api/"}

source_suffix = ".rst"
master_doc = "index"

add_function_parentheses = True
add_module_names = False
autosectionlabel_prefix_document = True

# HTML output
html_theme = "sphinx_immaterial"
html_theme_options = {
    "version_dropdown": True,
    "version_info": [
        {"version": "2.0", "title": "2.0", "aliases": ["latest"]},
        {"version": "1.0", "title": "1.0", "aliases": []},
        {"version": "0.9", "title": "0.9", "aliases": []},
    ],
}
html_static_path = ["_static"]
html_css_files = ["custom.css"]
