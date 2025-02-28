Installation
============

DTCC Platform can be installed using `pip
<https://pypi.org/project/pip/>`_.

To install from the `Python Package Index (PyPI)
<https://pypi.org/>`_::

   $ pip install dtcc

To install from the source directory::

   $ pip install .

.. note::

   For reliable installation and to avoid conflicts with your system Python,
   please create and activate a virtual environment before running any pip
   install commands. This approach is now required by modern packaging
   standards (see `PEP 668 <https://www.python.org/dev/peps/pep-0668/>`_).

   For example, on Unix systems you can run::

      $ python -m venv .venv
      $ source .venv/bin/activate
      $ pip install dtcc

   On Windows, activate the environment with::

      > python -m venv .venv
      > .venv\Scripts\activate
      > pip install dtcc
