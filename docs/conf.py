import os
import sys

sys.path.insert(0, os.path.abspath("../"))

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_immaterial",
    "sphinx_immaterial.apidoc.python.apigen",
]

source_suffix = ".rst"
master_doc = "index"

html_theme = "sphinx_immaterial"
html_theme_options = {"font": False}
python_apigen_modules = {"dtcc": "_api/"}

add_function_parentheses = True
add_module_names = False
