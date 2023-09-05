Usage
=====

This section provides an overview of the usage and capabilities of
DTCC Platform. For more details, refer to the :ref:`Demos` and
:ref:`API Reference`.

Downloading demo data
---------------------

DTCC Platform provides a number of demo data sets that can be used for
demos and testing.

To download the demo data, run the following command::

    dtcc-download-demo-data

This will create a directory named ``data`` containing the
demo data sets.

.. note::

   For the following documentation, it is assumed that you have downloaded the
   demo data. It is also assumed that you have installed the ``dtcc`` Python
   module on your system by following the :ref:`Installation` instructions.

Importing the DTCC Python module
--------------------------------

The following Python code imports all (main) classes and functions from the DTCC Python module:

.. code:: python

    from dtcc import *

This will for example import the functions ``load_pointcloud()`` and ``build_city()`` that are discussed in more detail below.

You may instead choose to import the ``dtcc`` module (not its contents) by the following code:

.. code:: python

    import dtcc

In this case, you need to prefix all functions and classes with ``dtcc.``. For example, the ``load_pointcloud()`` function is then called as ``dtcc.load_pointcloud()``.

.. note::

    For the following documentation, it is assumed that you have imported all the main classes and functions from the DTCC Python module by ``from dtcc import *``.

Loading and saving data
-----------------------

DTCC Platform can load (import) data from a number of formats into the native
DTCC data model. Data can also be saved (exported) to a number of formats.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

The command-line tool ``dtcc-convert`` provides a simple way to convert data files from one format to another::

  dtcc-convert [--from=<format>] [--to=<format>] input.x output.y

For example, a point cloud may be converted from LAS to LAZ format by the following command::

  dtcc-convert pointcloud.las pointcloud.laz

Python interface
^^^^^^^^^^^^^^^^

To load data from file, use the ``load_*()`` functions, for example:

.. code:: python

    from dtcc import *
    pointcloud = load_pointcloud("data/helsingborg-residential-2022/pointcloud.las")

To save data to file, use the ``.save()`` method, for example:

.. code:: python

    pointcloud.save("pointcloud.las")

Alternatively, the ``save_*()`` functions may be used, for example:

.. code:: python

    save_pointcloud(pointcloud, "pointcloud.las")

Data formats
^^^^^^^^^^^^

The following tables summarizes the supported input and output formats for the ``load_*()`` and ``save_*()`` functions.

.. list-table::
   :widths: 20 40 40
   :header-rows: 1

   * - Data type
     - Input formats
     - Output formats
   * - ``PointCloud``
     - ``.pb``, ``.pb2``, ``.las``, ``.laz``
     - ``.pb``, ``.pb2``, ``.las``, ``.laz``
   * - ``City``
     - ``.pb``, ``.pb2``, ``.shp``
     - ``.pb``, ``.pb2``
   * - ``Mesh``
     - ``.pb``, ``.pb2``, ``.obj``, ``.ply``, ``.stl``, ``.vtk``, ``.vtu``, ``.dae``, ``.fbx``
     - ``.pb``, ``.pb2``, ``.obj``, ``.ply``, ``.stl``, ``.vtk``, ``.vtu``, ``.gltf``, ``.gltf2``, ``.glb``, ``.dae``, ``.fbx``

To print which formats are supported by a given function, use the ``print_*_io()`` functions, for example:

.. code:: python

    print_mesh_io()

Building city models
--------------------

DTCC Platform provides a number of tools for building city models from
raw data, both from the command-line and from Python.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

The command-line tool ``dtcc-build`` builds a city model from a given data
directory and stores the generated city model as several mesh and data files in
the same directory. The following example illustrates how to build a city model
for the dataset ``helsingborg-residential-2022`` included as part of the demo
data::

    dtcc-build data/helsingborg-residential-2022

The single parameter to ``dtcc-build`` in this example is a directory of raw
data sources. If no argument is given, it is assumed that the data sources are
in the current working directory. The above example is thus equivalent to the
following::

    cd data/helsingborg-residential-2022
    dtcc-build

The data directory must contain the following input data:

* Point cloud data in `LAS/LAZ format <https://en.wikipedia.org/wiki/LAS_file_format>`_ consisting of one or more files
  with suffix ``.las`` or ``.laz``.
* Building footprints in `shapefile format <https://en.wikipedia.org/wiki/Shapefile>`_  named ``footprints.[shp,shx,dbf,prj,cpg]``.
* Parameters used to control the city model generation stored
  as a JSON file named ``parameters.json`` (optional).

After the city model has been built, the generated data files can be found in the specified data directory. By default, the data will be saved in
`Protobuf format <https://en.wikipedia.org/wiki/Protocol_Buffers>`_. The following files will be generated:

* ``city.pb`` - city model in Protobuf format
* ``ground_mesh.pb`` - a (triangular) mesh of the ground (excluding buildings)
* ``building_mesh.pb`` - a (triangular) mesh of the buildings (excluding ground)
* ``volume_mesh.pb`` - a (tetrahedral) mesh of the city (the empty space between the ground, the buildings, and an enclosing bounding box)
* ``volume_mesh_boundary.pb`` - a (triangular) mesh of the boundary of the volume mesh (including both the ground and the buildings)

The ``dtcc-build`` command accepts a number of parameters that can be
used to control the generation of the city model, for example::

    dtcc-build --mesh_resolution 20.0 --domain_height 75.0 data/helsingborg-residential-2022

To print a list of available parameters, use the following command::

    dtcc-build --help

See the :ref:`Parameters` section below for more details.

Python interface
^^^^^^^^^^^^^^^^

To build a city model from the Python interface, use the ``build()`` command, which is equivalent to running the ``dtcc-build`` command on the command-line:

.. code:: python

    # Set parameters
    p = parameters.default()
    p["data_directory"] = "data/helsingborg-residential-2022"
    p["mesh_resolution"] = 20.0
    p["domain_height"] = 75.0

    # Build city model
    build(p)

In this example, we first create a dictionary of default parameters by calling
``parameters.default()`` and then set the essential ``data_directory``
parameter. We also set the parameter ``mesh_resolution`` to 20.0 (meters),
telling the mesh generator to generate a mesh with a maximum cell size of 20.0
meters, and the ``domain_height`` parameter to 75.0 (meters), telling the mesh
generator to generate a mesh with a domain height of 75.0 meters. Finally, we
call ``build()`` with the parameters to build the city model with the given
parameters.

For more fine-grained control of the city model generation, the commands
``build_city()``, ``build_mesh()``, and ``build_volume_mesh`` can be used. To
use these commands, we must first calculate the domain bounds and load the raw
data:

.. code:: python

    origin, bounds = calculate_bounds(buildings_path, pointcloud_path, p)
    city = load_city(buildings_path, bounds=bounds)
    pointcloud = load_pointcloud(pointcloud_path, bounds=bounds)

where ``buildings_path`` and ``pointcloud_path`` are the paths to the raw data files.

We can then build the city model by calling the ``build_city()`` command:

.. code:: python

    city = build_city(city, pointcloud, bounds, p)

Once the city model has been built, we may proceed to build (triangular) surface meshes and (tetrahedral) volume meshes for the city model:

.. code:: python

    ground_mesh, building_mesh = build_mesh(city, p)
    volume_mesh, volume_mesh_boundary = build_volume_mesh(city, p)

The data may then be save to file using the ``.save()`` method and viewed using
the ``.view()`` method, for example:

.. code:: python

    city.save("city.pb")
    city.view()

For a complete example, see the :ref:`build_city_and_meshes` demo.

.. note::

   Currently, only LoD1.2 city models are supported but work in
   progress is aiming to extend the capabilities to generate both
   LoD1.3 and LoD2.x models.

Parameters
^^^^^^^^^^

The city model and mesh generation may be controlled using a set of parameters.

When working from the command-line, the parameters may be specified either by passing them as command-line arguments or by storing them in a JSON file named ``parameters.json`` in the data directory. In a previous example, we saw the the following command-line call::

    dtcc-build --mesh_resolution 20.0 --domain_height 75.0 data/helsingborg-residential-2022

This is equivalent to the following JSON file present in the data directory::

    {
        "mesh_resolution": 20.0,
        "domain_height": 75.0
    }

When working from Python, the parameters are specified as a Python dictionary. The parameters in the above example may be specified by the following Python code::

    p = parameters.default()
    p["mesh_resolution"] = 20.0
    p["domain_height"] = 75.0

The list of available parameters can be viewed from the command-line by ``dtcc-build --help`` or from Python by ``print(parameters.default())``.

Some of the most important parameters are explained below.

.. list-table::
   :widths: 30 50 20
   :header-rows: 1

   * - Parameter name
     - Description
     - Default value
   * - ``data_directory``
     - Path to directory containing input data
     - ``""``
   * - ``output_directory``
     - Path to directory where output data will be stored
     - ``""``
   * - ``build_mesh``
     - Flag indicating whether to build ground and building meshes
     - ``True``
   * - ``build_volume_mesh``
     - Flag indicating whether to build volume mesh
     -  ``True``
   * - ``auto_domain``
     - Flag indicating whether to automatically calculate the domain bounds
     - ``True``
   * - ``x_0``
     - x-coordinate of origin
     - ``0.0``
   * - ``y_0``
     - y-coordinate of origin
     - ``0.0``
   * - ``x_min``
     - Minimum x-coordinate of domain relative to origin
     - ``0.0``
   * - ``y_min``
     - Minimum y-coordinate of domain relative to origin
     - ``0.0``
   * - ``x_max``
     - Maximum x-coordinate of domain relative to origin
     - ``0.0``
   * - ``y_max``
     - Maximum y-coordinate of domain relative to origin
     - ``0.0``
   * - ``mesh_resolution``
     - Maximum cell size of generated meshes
     - ``10.0``
   * - ``domain_height``
     - Height of domain (bounding box)
     - ``100.0``

Visualising data
----------------

The DTCC platform provides an integrated viewer which has the capability
to display large quatities of geometry, including meshes and point clouds.

To visualise a point cloud colored by the x-position of the points:

.. code:: python

    from dtcc_io import pointcloud
    filename_pc = '../../../data/models/pointcloud.las'
    pc = pointcloud.load(filename_pc)
    color_data = pc.points[:,0]
    pc.view(pc_data = color_data)

To visualise a mesh without data (default coloring schema will be vertex
z-value):

.. code:: python

    from dtcc_io import meshes
    filename_mesh = '../../../data/models/mesh.obj'
    mesh = meshes.load_mesh(filename_mesh)
    mesh.view()

To visualise a point cloud and a mesh in the same window:

.. code:: python

    from dtcc_io import meshes
    from dtcc_io import pointcloud
    filename_mesh = '../../../data/models/mesh.obj'
    filename_pc = '../../../data/models/pointcloud.csv'
    pc = pointcloud.load(filename_pc)
    mesh = meshes.load_mesh(filename_mesh)
    pc.view(mesh=mesh)

The same principle works the other way around, where the pointclode is
added as an argument to the mesh viewing function call:

.. code:: python

    from dtcc_io import meshes
    from dtcc_io import pointcloud
    filename_mesh = '../../../data/models/mesh.obj'
    filename_pc = '../../../data/models/pointcloud.csv'
    pc = pointcloud.load(filename_pc)
    mesh = meshes.load_mesh(filename_mesh)
    mesh.view(pc=pc)


DTCC Viewer can also be used to visualise multiple meshes and point clouds
using a slightly different approch:

.. code:: python

    from dtcc_io import meshes
    from dtcc_io import pointcloud

    window = Window(1200, 800)

    # Import meshes to be viewed
    mesh_a = meshes.load_mesh("../../../data/models/CitySurfaceA.obj")
    mesh_b = meshes.load_mesh("../../../data/models/CitySurfaceB.obj")

    # Create data for coloring each mesh
    mesh_data_a = mesh_a.vertices[:, 1]
    mesh_data_b = mesh_b.vertices[:, 0]
    meshes_imported = [mesh_a, mesh_b]

    # Import point clodus to be viewed
    pc_a = pointcloud.load("../../../data/models/PointCloud_HQ_A.csv")
    pc_b = pointcloud.load("../../../data/models/PointCloud_HQ_B.csv")

    # Create data for coloring each mesh
    pc_data_a = pc_a.points[:, 0]
    pc_data_b = pc_b.points[:, 1]
    pcs_imported = [pc_a, pc_b]

    # Calculate common recentering vector base of the bounding box of all combined vertices.
    recenter_vec = calc_multi_geom_recenter_vector(meshes_imported, pcs_imported)

    # Create MeshData object where all the data for each mesh is formated for OpengGL calls
    mesh_data_obj_a = MeshData("mesh A", mesh_a, mesh_data_a, recenter_vec)
    mesh_data_obj_b = MeshData("mesh B", mesh_b, mesh_data_b, recenter_vec)
    mesh_data_list = [mesh_data_obj_a, mesh_data_obj_b]

    # Create PointCloudData object where all the data for each pc is formated for OpengGL calls
    pc_data_obj_a = PointCloudData("point cloud A", pc_a, pc_data_a, recenter_vec)
    pc_data_obj_b = PointCloudData("point cloud B", pc_b, pc_data_b, recenter_vec)
    pc_data_list = [pc_data_obj_a, pc_data_obj_b]


    window.render_multi(mesh_data_list, pc_data_list)

Viewer controls
^^^^^^^^^^^^^^^

Once the DTCC Viewer is running and a graphics window is the viewport
navigation is done with the mouse according to:

- `Left mouse button` - Rotate the view around the camera target
- `Right mouse button` - Panning the view, thus moving the camera target
- `Scroll` - Zoom in and out at the current camera target

A GUI is also created with global controls for the whole scene under
apperance which includes things like (background color etc). Individual
GUI components are also created for each Mesh and Point Cloud that is
on display.
