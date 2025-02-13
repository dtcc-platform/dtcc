import os

# Determine whether to skip API docs generation.
skip_api = os.environ.get("NO_API", "0") == "1"

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

html_theme = "sphinx_immaterial"
html_theme_options = {
    "font": False,
    "palette": {
        "scheme": "default",
    },
}
html_static_path = ["_static"]
html_css_files = ["custom.css"]
