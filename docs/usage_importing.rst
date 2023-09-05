Importing the Python module
===========================

The following Python code imports all (main) classes and functions from the DTCC Python module:

.. code:: python

    from dtcc import *

This will, for example, import the functions ``load_pointcloud()`` and ``build_city()`` that are discussed in more detail below.

You may instead choose to import the ``dtcc`` module (not its contents) by the following code:

.. code:: python

    import dtcc

In this case, you need to prefix all functions and classes with ``dtcc.``. For example, the ``load_pointcloud()`` function is then called as ``dtcc.load_pointcloud()``.

.. note::

    For the following documentation, it is assumed that you have imported all the main classes and functions from the DTCC Python module by ``from dtcc import *``.

