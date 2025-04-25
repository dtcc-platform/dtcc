Development
===========

Coding style
------------

DTCC Platform uses the coding style native to each language or domain.
This means, e.g., following the `Style
Guide <https://peps.python.org/pep-0008/>`__ for Python code and the `C++
Core
Guidelines <https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines>`__
for C++ code.

The following table summarizes the naming conventions used for DTCC
Platform.

======== ================ ================ ===============
\        Python           C++              JavaScript
======== ================ ================ ===============
Variable ``snake_case``   ``snake_case``   ``camelCase``
Function ``snake_case()`` ``snake_case()`` ``camelCase()``
Class    ``PascalCase``   ``PascalCase``   ``PascalCase``
Module   ``snake_case``
======== ================ ================ ===============

In addition to this, DTCC Platform uses ``kebab-case`` for naming API
endpoints, branches and scripts. For JSON ``snake_case`` is used.

Scripts and binaries that are installed on the system should be named
``dtcc-foo-bar``. Scripts that are *not* installed on the system
(typically small utility scripts) should be named ``foo-bar`` (without
``dtcc-``).

Code formatting
---------------

For Python code we use the `Black <https://github.com/psf/black>`_ formatter.
All Python code should be run through Black with default settings before
committing. or instructions on how to set it up for Visual Studio Code, see for
example `these instructions
<https://dev.to/adamlombard/how-to-use-the-black-python-code-formatter-in-vscode-3lo0>`_.

The following settings should be used in VS Code::

    // Python Settings
    "[python]": {
      "editor.defaultFormatter": "ms-python.black-formatter"
    },

    // C++ Settings
    "[cpp]": {
      "editor.defaultFormatter": "xaver.clang-format"
    },
    "C_Cpp.clang_format_fallbackStyle": "none",

The following settings are used for clang-format (``.clang-format`` in
``dtcc-core`` repo)::

    BreakBeforeBraces: Allman
    IndentWidth: 2
    UseTab: Never
    ColumnLimit: 100

Git practices
-------------

DTCC Platform uses the following Git practices:

-  The main (release) branch is named ``main``.
-  The development branch is named ``develop``.
-  All work should take place in separate branches (not directly in
   ``develop`` and certainly not in ``main``).
-  Branches for development (new features) should be named
   ``dev/branch-name`` where ``branch-name`` is a free form descriptive
   name.
-  Branches for fixes (bugs, small things) should be named
   ``fix/branch-name`` where ``branch-name`` is a free form descriptive
   name.
-  Branches that will (likely) not be merged but kept for reference
   should be named ``old/branch-name`` where ``branch-name`` is a free
   form descriptive name.
-  Note that hyphens should be used for naming (not underscore).
-  When the work is done, make a pull request for merging the branch
   into ``develop``.
-  When the work has been merged, the branch should be deleted to keep
   things tidy.
-  When making a release, ``develop`` is merged into ``main`` and a
   release is made from ``main``.

Versioning
----------

DTCC Platform uses semantic versioning (SemVer). It uses a three-part
number system in the format of MAJOR.MINOR.PATCH, where:

-  MAJOR version is incremented for incompatible API changes.
-  MINOR version is incremented for new features that are
   backwards-compatible.
-  PATCH version is incremented for backwards-compatible bug fixes.

The version number is set in the ``pyproject.toml`` file for each repo.

During early development (before the release of 1.0.0) API changes are
expected to happen often and will not lead to incrementation of the
MAJOR number (which stays at 0). During this phase, the MINOR number
will work in the same way as the MAJOR version; that is, the MINOR
number should be incremented for incompatible API changes. Note that the
MINOR number may then advance well beyond 9 (e.g. 0.29.1, 0.31.3, etc)
before we release 1.0.0.

During early development, the MINOR number should stay the same for all
projects (repos) and post 1.0.0, the MAJOR number should stay the same.

Releasing new versions
----------------------

New versions should be released from the ``main`` branch (after ``develop``) has been merged into ``main``. The following steps should be taken:

1. Update the version number in ``pyproject.toml``.
2. Set the correct dependencies in ``pyproject.toml``. Note that dependencies should be to released versions of all DTCC packages (not Git branches).
3. Commit the changes with commit message ``Bump version number to X.Y.Z``.
4. Add a tag with the version number: ``git tag vX.Y.Z``
5. ... pypi, announce, etc.

Writing documentation
---------------------

Documentation is automatically extracted (by Sphinx) from Python docstrings.
ChatGPT can assist in writing the docstrings. The following prompt can be
helpful when generating the docstrings::

   I want you to generate docstrings for Python code. The docstrings should
   be consice, consistent, and informative. The docstrings should be in the
   format of the Sphinx documentation system (restructured text) and follow
   NumPy docstring style according to the following templates from the page
   https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html:

   def function_with_types_in_docstring(param1, param2):
      """Example function with types documented in the docstring.

      :pep:`484` type annotations are supported. If attribute, parameter, and
      return types are annotated according to `PEP 484`_, they do not need to be
      included in the docstring:

      Parameters
      ----------
      param1 : int
         The first parameter.
      param2 : str
         The second parameter.

      Returns
      -------
      bool
         True if successful, False otherwise.
      """

   def function_with_pep484_type_annotations(param1: int, param2: str) -> bool:
      """Example function with PEP 484 type annotations.

      The return type must be duplicated in the docstring to comply
      with the NumPy docstring style.

      Parameters
      ----------
      param1
         The first parameter.
      param2
         The second parameter.

      Returns
      -------
      bool
         True if successful, False otherwise.
      """

   class ExampleClass:
      """The summary line for a class docstring should fit on one line.

      If the class has public attributes, they may be documented here
      in an ``Attributes`` section and follow the same formatting as a
      function's ``Args`` section. Alternatively, attributes may be documented
      inline with the attribute's declaration (see __init__ method below).

      Properties created with the ``@property`` decorator should be documented
      in the property's getter method.

      Attributes
      ----------
      attr1 : str
         Description of `attr1`.
      attr2 : :obj:`int`, optional
         Description of `attr2`.

      """

      def __init__(self, param1, param2, param3):
         """Example of docstring on the __init__ method.

         The __init__ method may be documented in either the class level
         docstring, or as a docstring on the __init__ method itself.

         Either form is acceptable, but the two should not be mixed. Choose one
         convention to document the __init__ method and be consistent with it.

         Note
         ----
         Do not include the `self` parameter in the ``Parameters`` section.

         Parameters
         ----------
         param1 : str
               Description of `param1`.
         param2 : list(str)
               Description of `param2`. Multiple
               lines are supported.
         param3 : :obj:`int`, optional
               Description of `param3`.

         """
         self.attr1 = param1
         self.attr2 = param2
         self.attr3 = param3  #: Doc comment *inline* with attribute

         #: list(str): Doc comment *before* attribute, with type specified
         self.attr4 = ["attr4"]

         self.attr5 = None
         """str: Docstring *after* attribute, with type specified."""

      def example_method(self, param1, param2):
         """Class methods are similar to regular functions.

         Note
         ----
         Do not include the `self` parameter in the ``Parameters`` section.

         Parameters
         ----------
         param1
               The first parameter.
         param2
               The second parameter.

         Returns
         -------
         bool
               True if successful, False otherwise.

         """
         return True

      In summary, the docstrings should be formatted as follows:

      For classes:

      * Start with a short description (one line).
      * Then give a detailed description over several lines (if possible).
      * List attributes under the Attributes section.

      For functions:

      * Start with a short description (one line).
      * List parameters under the Parameters section.
      * Detail the return type and its description under the Returns section (if there's a return value).

      For methods:

      * Start with a short description (one line).
      * List parameters under the Parameters section (excluding self for class methods).
      * Detail the return type and its description under the Returns section (if there's a return value).

      For properties:

      * Start with a short description (one line).
      * Detail the return type and its description under the Returns section.

      I will supply a number of functions and class definitions and want you to return
      the corresponding docstrings. Please provide docstrings for all the provided
      code (not just some of it) and don't forget to document class attributes under
      the Attributes section.

Use ChatGPT to generate the docstrings but make sure to check that the
docstrings make sense and are consistent with the templates above. Also be
careful to only copy the docstrings into the code (don't modify the code itself).

Tips & tricks
-------------

Remote development in VS Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the left-side menu, go to Remote Explorer and press the + sign on the SSH
line. Add your SSH connection in the following format::

    user@develop.dtcc.chalmers.se

This should add the `develop` server to the connection list and you may connect to it by clicking on the right arrow next to its name.

You may then open files on the remote server using the regular Open command. You
may also open a remote terminal using the top menu: Terminal --> New Terminal.

Handling line endings on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are using Windows, you might want to make sure that Git does
not convert Unix-style file endings on checkout. This can be
accomplished by::

    git config --global dtcc-builder.autocrlf false
