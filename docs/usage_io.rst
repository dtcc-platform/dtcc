Loading and saving data
=======================

DTCC Platform can load (import) data from a number of formats into the native
DTCC data model. Data can also be saved (exported) to a number of formats.

Command-line interface
----------------------

The command-line tool ``dtcc-convert`` provides a simple way to convert data files from one format to another::

  dtcc-convert [--from=<format>] [--to=<format>] input.x output.y

For example, a point cloud may be converted from LAS to LAZ format by the following command::

  dtcc-convert pointcloud.las pointcloud.laz

Python interface
----------------

To load data from file, use the ``load_*()`` functions, for example:

.. code:: python

    pointcloud = load_pointcloud("data/helsingborg-residential-2022/pointcloud.las")

To save data to file, use the ``.save()`` method, for example:

.. code:: python

    pointcloud.save("pointcloud.las")

Alternatively, use the ``save_*()`` function, for example:

.. code:: python

    save_pointcloud(pointcloud, "pointcloud.las")

Data formats
------------

The following table summarizes the supported input and output formats for the ``load_*()`` and ``save_*()`` functions.

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
     - ``.pb``, ``.pb2``, ``.shp``, ``.gpkg``, ``.geojson``
     - ``.pb``, ``.pb2``, ``.shp``, ``.gpkg``, ``.geojson``
   * - ``Mesh``
     - ``.pb``, ``.pb2``, ``.obj``, ``.ply``, ``.stl``, ``.vtk``, ``.vtu``, ``.dae``, ``.fbx``
     - ``.pb``, ``.pb2``, ``.obj``, ``.ply``, ``.stl``, ``.vtk``, ``.vtu``, ``.gltf``, ``.gltf2``, ``.glb``, ``.dae``, ``.fbx``

To print which formats are supported by a given function, use the ``print_*_io()`` functions, for example:

.. code:: python

    print_mesh_io()
