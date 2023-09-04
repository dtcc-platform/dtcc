Usage
=====

This section provides an overview of the usage and capabilities of
DTCC Platform. For more details, refer to the :ref:`Demos` and
:ref:`API Reference`.

Downloading demo data
---------------------

DTCC Platform provides a number of demo data sets that can be used for
demos and testing.

To download the demo data sets, run the following command::

    dtcc-download-demo-data

This will create a directory named ``dtcc-demo-data`` containing the
demo data sets.

.. note::

   For the following documentation, it is assumed that you have
   downloaded the demo data sets and entered the demo data directory
   (``cd dtcc-demo-data``). It is also assumed that you have installed
   the ``dtcc`` Python module on your system by following the
   :ref:`Installation` instructions.

Loading and saving data
-----------------------

DTCC Platform can load (import) data from a number of formats into the native
DTCC data model. Data can also be saved (exported) to a number of formats.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

Put documentation here for the command-line interface::

  dtcc-convert [--from=<format>] [--to=<format>] input.x output.y

Python interface
^^^^^^^^^^^^^^^^

Put documentation here for Python interface.

.. code:: python

    from dtcc import *
    pc = load_pointcloud(...)

Data formats
^^^^^^^^^^^^

List supported formats here and explain how to print which formats are
available from Python.

**@dag Write docs for dtcc-io here**

**@dag Note old copied from dtcc-io further down on this page**

Building city models
--------------------

DTCC Platform provides a number of tools for building city models from
raw data, both from the command-line and from Python.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

To build a city model using the command-line interface, use the
``dtcc-build`` command, for example::

  dtcc-build HelsingborgResidential2022

The single parameter to ``dtcc-build`` in this example is a directory
of raw data sources. If no argument is given, it is assumed that the
data sources are in the current working directory. The above example
is thus equivalent to the following::

  cd HelsingborgResidential2022
  dtcc-build

The `dtcc-build` command accepts a number of parameters that can be
used to control the generation of the city model, for example::

  dtcc-build --mesh_resolution 5.0 --domain_height 75.0 HelsingborgResidential2022

To print a list of available parameters, use the following command::

  dtcc-build --help

See also the :ref:`Parameters` section below for more details.

Python interface
^^^^^^^^^^^^^^^^

The corresponding command in Python is ``build()``.

.. code:: python

    from dtcc import *
    pc = load_pointcloud(...)
    city = build(pc)

.. note::

   Currently, only LoD1.2 city models are supported but work in
   progress is aiming to extend the capabilities to generate both
   LoD1.3 and LoD2.x models.

Parameters
^^^^^^^^^^

To see a list of parameters::

  dtcc-build --help

Parameters can also be set by ``parameters.json`` if present in the
data directory. For example, the above example can be done with JSON
file::

  {
     "foo": ...,
     "bar": ...
  }


**THE FOLLOWING TEXT IS COPIED FROM dtcc-builder AND NEEDS EDITING**

## Overview


    dtcc-generate-citymodel
    dtcc-generate-mesh

The first of these programs is used to [generate city models from raw
data](#generating-city-models) and the second program is used to
[generate meshes for a city model](#generating-meshes). Both programs
are described in detail below.


The output data may be found in the corresponding subdirectory of the
`data` directory and consist of several data files in JSON and
[Paraview](https://www.paraview.org/) format. Both the data formats
and how to visualize the generated city models and meshes are
described in detail below.

## Generating city models (`dtcc-generate-citymodel`)

The program `dtcc-generate-citymodel` is used to generate a city model
from a set of point clouds and cadastral data.

### Input data

The following input data are needed:

* **Point cloud data** in LAS/LAZ format consisting of one or more files
  with suffix `.las` or `.laz`.
* **Cadastral data** in [shapefile format](https://en.wikipedia.org/wiki/Shapefile)
  named `PropertyMap.[shp,shx,dbf,prj,cpg]`.
* **Parameters** used to control the city model generation stored
  as a JSON file named `Parameters.json` (optional).

If no command-line argument is given, it is assumed that the current
working directory contains the input data:

    dtcc-generate-citymodel

If a directory is given as command-line argumennt, the given directory
is searched for the input data:

    dtcc-generate-citymodel <path to data directory>

If a parameter file is given as argument, the specified
`DataDirectory` parameter is searched for the input data:

    dtcc-generate-citymodel <path to parameter file>

### Output data

* `CityModel.json` - city model in DTCC JSON format
* `DSM.json` - digital surface map in DTCC JSON format
* `DSM.vts` - digital surface map in VTK structured grid format
* `DTM.json` - digital terrain map in DTCC JSON format
* `DTM.vts` - digital terrain map in VTK structured grid format

In addition, timings and parameters are stored as
`dtcc-generate-citymodel-timings.json` and
`dtcc-generate-citymodel-parameters.json`.

## Generating meshes (`dtcc-generate-mesh`)

The program `dtcc-generate-mesh` is used to generate meshes from a
city model and a digital terrain map.

### Input data

The following input data are needed:

* **City model** in DTCC JSON format named `CityModel.json`.
* **Digital terrain map** in DTCC JSON format named `DTM.json`.
* **Parameters** used to control the mesh generation stored
  as a JSON file named `Parameters.json` (optional).

If no command-line argument is given, it is assumed that the current
working directory contains the input data:

    dtcc-generate-mesh

If a directory is given as command-line argumennt, the given directory
is searched for the input data:

    dtcc-generate-mesh <path to data directory>

If a parameter file is given as argument, the specified
`DataDirectory` parameter is searched for the input data:

    dtcc-generate-mesh <path to parameter file>

### Output data

- `CityModelSimple.json` - simplified city model in DTCC JSON format
- `GroundSurface.json` - surface mesh of ground in DTCC JSON format
- `GroundSurface.vtu` - surface mesh of ground in VTK unstructured grid format
- `BuildingSurface.json` - surface mesh of buildings in DTCC JSON format
- `BuildingSurface.vtu` - surface mesh of buildings in VTK unstructured grid format
- `CitySurface.json` - surface mesh of ground and buildings in DTCC JSON format
- `CitySurface.vtu` - surface mesh of ground and buildings in VTK unstructured grid format
- `CityMesh.json` - volume mesh of city in DTCC JSON format
- `CityMesh.vtu` - volume mesh of city in VTK unstructured grid format

In addition, timings and parameters are stored as
`dtcc-generate-mesh-timings.json` and
`dtcc-generate-mesh-parameters.json`.

## Visualizing results

Generated data files in DTCC JSON format may be opened and visualized
using [DTCC Viewer](https://viewer.dtcc.chalmers.se).

Generated data files in VTK structured/unstructured grid format may be
opened and visualized using [Paraview](https://www.paraview.org/).

## Parameters

DTCC Builder may be controlled using a set of parameters specified in
JSON format. The parameters file may either be supplied as a
command-line argument or stored in a file named `Parameters.json` in
the data directory.

All data files are assumed to be located in a directory determined by
the parameter `DataDirectory`:

    DataDirectory = directory for input data files

Generated data files will be stored in a directory determined by the
parameter `OutputDirectory`:

    OutputDirectory = directory for generated data files

When parsing data from original data files (LAS point clouds and SHP
files), a nonzero origin may be specified to offset the coordinate
system relative to the origin. This has the advantage that very large
values for the coordinates may be avoided (which is good for numerical
stability):

    X0 = x-coordinate of new origin
    Y0 = y-coordinate of new origin

The offset `(X0, Y0)` is subtracted from the original coordinates
during processing. In the simplest case, the offset should be set to
the coordinates of the lower left (south-west) corner of the domain
covered by the data.

Height maps, city models, and meshes are generated for a rectangular
domain with coordinates relative to the new origin specified by `X0`
and `Y0`:

    XMin = x-coordinate for lower left corner
    YMin = y-coordinate for lower left corner
    XMax = x-coordinate for upper right corner
    YMax = y-coordinate for upper right corner

In the simplest case, the lower left corner should be set to `(XMin,
YMin) = (0, 0)` and the upper right corner should be set to `(XMax,
YMax) = (Width, Height)`.

Alternatively, the domain may be determined by the bounding box of the
point cloud(s) by. If `AutoDomain` is `true`, then `XMin`, `YMin`,
`XMax`, `YMax` are automatically determined (and their parameter
values ignored):

    AutoDomain = true/false

When generating elevation models from LAS point cloud data, the
`ElevationModelResolution` parameter determines the resolution of the grid
onto which the height map is sampled:

    ElevationModelResolution = resolution of elevation models

When generating city models from SHP file data, the
`MinimalBuildingDistance` parameter determines a minimal distance
between buildings. Buildings that are closer than the specified
distance are automatically merged to avoid overlapping buildings or
buildings that are very close (which may otherwise upset the mesh
generation):

    MinBuildingDistance = minimal distance between buildings

When generating the volume mesh, the `DomainHeight` parameter
determines the height of the domain relative to the mean ground level:

    DomainHeight = height of computational domain (volume mesh)

When generating both volume and visualization meshes, the
`MeshResolution` parameter determines the maximum size (diameter) of
the mesh cells:

    MeshResolution = resolution of computational mesh (mesh size)

Both volume and visualization meshes may be generated with or without
displacing the ground level outside of buildings. If the `FlatGround`
parameter is set to `true`, then the ground is kept flat:

    FlatGround = true / false

The surface mesh generation produces an additional smoothed version of
the ground surface. The number of smoothing iterations is controlled
by the `GroundSmoothing` parameter:

    GroundSmoothing = number of smoothing iterations

> **Note**: The list of parameters above is only partly complete since
experimental parameters may be added/removed during development. For
a complete list of  parameters, refer to the parameter files
`dtcc-generate-[citymodel,mesh].json` generated by running the demo.

DTCC Builder is a mesh generator for automatic, efficient, and robust
mesh generation for large-scale city modeling and simulation.

Using standard and widely available raw data sources in the form of
point clouds and cadastral data, DTCC Builder generates high-quality
3D surface and volume meshes, suitable for both visualization and
simulation. In particular, DTCC Builder is capable of generating
large-scale, conforming tetrahedral volume meshes of cities suitable
for finite element (FEM) simulation.


The mesh generation algorithm relies on two key ideas. First, the mesh
generation is reduced from a 3D problem to a 2D problem by taking
advantage of the cylindrical geometry of extruded 2D footprints; a 2D
mesh respecting the boundaries of the buildings is generated by a 2D
mesh generator and then layered to form a 3D mesh. Second, the 3D mesh
is adapted to the geometries of building and ground by solving a
partial differential equation (PDE) with the ground and building
heights as boundary conditions (mesh smoothing). Together these two
ideas enable the creation of a both efficient and robust pipeline for
automated large-scale mesh generation from raw data. The algorithm is
described in detail in the paper [Digital twins for city simulation:
Automatic, efficient, and robust mesh generation for large-scale city
modeling and simulation](TBD).

![](images/demo-majorna.jpg)
*Surface mesh of an area (Majorna) in Gothenburg, generated with DTCC Buider.*

![](images/demo-majorna-zoom.jpg)
*Detail of surface mesh of an area (Majorna) in Gothenburg, generated with DTCC Builder.*

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


**THE FOLLOWING TEXT IS COPIED FROM dtcc-io AND NEEDS EDITING**

# Usage
```python
import dtcc_io as io
foo = io.load_foo("my_data.foo")
foo = io.load_foo("my_data.pb")
io.save_foo(foo, "my_data.foo")
```

dtcc_io handles loading and saving both our protobuf messages as well as popular file formats to an from our data models.

we currently have the following function:

- `[load|save]_mesh` supports obj, stl, vtu, gltf2, glb
- `[load|save]_volumemesh` support vtk, vtu
- `[load|save]_pointcloud` supports las, laz, csv
- `[load|save]_citymodel` supports shp,geojson,gpkg
- `[load|save]_elevationmodel` supoprts tif
