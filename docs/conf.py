project = "DTCC Platform"
copyright = "Digital Twin Cities Centre 2023"
author = "Digital Twin Cities Centre"

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_immaterial",
    "sphinx_immaterial.apidoc.python.apigen",
]

source_suffix = ".rst"
master_doc = "index"

python_apigen_modules = {"dtcc": "_api/"}
add_function_parentheses = True
add_module_names = False

html_theme = "sphinx_immaterial"
html_theme_options = {
    "font": False,
    "palette": {"primary": "light-blue", "accent": "orange"},
}
