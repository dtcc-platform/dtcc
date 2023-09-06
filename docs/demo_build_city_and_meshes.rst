Demo: Build city and meshes
===========================

This demo can be found in the `demos directory
<https://github.com/dtcc-platform/dtcc/tree/develop/demos>`_. To run the demo,
type::

    $ python build_city_and_meshes.py

.. note::

    This demo requires the ``dtcc`` package to be installed. The demo also
    requires that you have run the command ``dtcc-download-demo-data`` to download the demo data used by the demo.

Purpose
-------

This demo illustrates how to build city models and meshes from raw data.

Step-by-step
------------

To use DTCC Platform, we first need to import the package in Python. We also choose to import ``Path`` from the ``pathlib`` package, which is useful for handling file paths.

.. code:: python

    from dtcc import *
    from pathlib import Path

We next need to set paths to the data that will be used. In the current demo, we
need to set a path to the buildings shapefile and also to the directory
containing the point cloud data.

.. code:: python

    data_directory = Path("data/helsingborg-residential-2022")
    buildings_path = data_directory / "footprints.shp"
    pointcloud_path = data_directory

The building process can be controlled via a number of parameters. For the
current demo, we will use the default parameters. For illustration purposes, we
also choose to set the ``auto_domain`` parameter to ``True``. This will
automatically calculate the domain bounds from the buildings shapefile and the
point cloud data (by taking the intersection of the bounds of the two data).

.. code:: python

    p = parameters.default()
    p["auto_domain"] = True

We next calculate the bounds from the buildings shapefile and the point cloud by
supplying the data paths and the parameters. The returned ``origin`` object is
the origin of the domain and the ``bounds`` object is the bounds of the domain.

.. code:: python

    origin, bounds = calculate_bounds(buildings_path, pointcloud_path, p)

We can now load the city model and the point cloud data. The ``load_city``
function takes the buildings shapefile path and the bounds as input. The
``load_pointcloud`` function takes the point cloud data directory path, and the
bounds as input.

.. code:: python

    city = load_city(buildings_path, bounds=bounds)
    pointcloud = load_pointcloud(pointcloud_path, bounds=bounds)

The city model can now be built from the loaded data. The ``build_city``
function takes the city model, the point cloud data, the bounds, and the
parameters as input.

.. code:: python

    city = build_city(city, pointcloud, bounds, p)

To build the meshes for the generated city model, we may call the two functions ``build_mesh`` and ``build_volume_mesh``. The ``build_mesh`` function returns one mesh for the ground and a separate mesh for the buildings. The ``build_volume_mesh`` function returns one tetrahedral volume mesh for the city volume (the empty space between the ground, the buildings and an enclosing bounding box) and a separate mesh for the boundary of the volume mesh.

.. code:: python

    ground_mesh, building_mesh = build_mesh(city, p)
    volume_mesh, volume_mesh_boundary = build_volume_mesh(city, p)

To save the city model and the meshes to file, we may call the ``save`` method on each object. The ``.save`` function takes the data path as input. We here choose to save the city model and the meshes to `Protobuf format <https://en.wikipedia.org/wiki/Protocol_Buffers>`_.

.. code:: python

    city.save(data_directory / "city.pb")
    ground_mesh.save(data_directory / "ground_mesh.pb")
    building_mesh.save(data_directory / "building_mesh.pb")
    volume_mesh.save(data_directory / "volume_mesh.pb")
    volume_mesh_boundary.save(data_directory / "volume_mesh_boundary.pb")

We may also view the city model and the point cloud data in the 3D viewer. To view the data, we call the ``.view`` method on each object.

.. code:: python

    city.view()
    pointcloud.view()

Complete code
-------------

The complete code for the demo is shown below.

.. literalinclude:: ../demos/build_city_and_meshes.py
  :language: python
