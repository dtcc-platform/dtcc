import os, toml

# Parse version from pyproject.toml
with open("../pyproject.toml", "r") as f:
    data = toml.load(f)
version = data["project"]["version"]

# General information about the project
project = "DTCC Platform"
author = "Digital Twin Cities Centre"
copyright = "Digital Twin Cities Centre (2025)"
release = version

# Determine whether to skip API docs generation.
skip_api = os.environ.get("NO_API", "0") == "1"

# Sphinx configuration
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "sphinx_immaterial",
]

# Skip or include API
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
html_title = f"DTCC Platform (v{version})"
html_theme_options = {
    "version_dropdown": True,
    "version_info": [
        {"version": f"v{version}", "title": f"v{version}", "aliases": []},
        {"version": "v0.7.0", "title": "v0.7.0", "aliases": []},
        {"version": "v0.6.0", "title": "v0.6.0", "aliases": []},
    ],
}
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_logo = "_static/dtcc-icon.svg"
