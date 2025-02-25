Data Formats
============

.. warning::

   This page is under construction. The content is incomplete and may contain errors.

   @dag Please fix this page!

Overview
--------

In preparation.

Supported Data Formats
----------------------

In preparation.

The following table summarizes the supported input and output formats for the ``load_*`` and ``save_*`` functions.

.. list-table::
   :widths: 20 40 40
   :header-rows: 1

   * - Data type
     - Input formats
     - Output formats
   * - ``PointCloud``
     - ``.pb``, ``.pb2``, ``.las``, ``.laz``, ``.csv``
     - ``.pb``, ``.pb2``, ``.las``, ``.laz``, ``.csv``
   * - ``City``
     - ``.pb``, ``.pb2``, ``.cityjson``
     - ``.pb``, ``.pb2``, ``.cityjson``
   * - ``Mesh``
     - ``.pb``, ``.pb2``, ``.obj``, ``.ply``, ``.stl``, ``.vtk``, ``.vtu``, ``.dae``, ``.fbx``, ``.gltf``, ``.gltf2``, ``.glb``
     - ``.pb``, ``.pb2``, ``.obj``, ``.ply``, ``.stl``, ``.vtk``, ``.vtu``, ``.gltf``, ``.gltf2``, ``.glb``, ``.dae``, ``.fbx``
   * - ``Footprints``
     - ``.pb``, ``.pb2``, ``.geojson``, ``.shp``, ``.gpkg``
     - ``.pb``, ``.pb2``, ``.geojson``, ``.shp``, ``.gpkg``
To print which formats are supported by a given function, use the ``print_*_io`` functions, for example:

.. code:: python

    print_mesh_io()
