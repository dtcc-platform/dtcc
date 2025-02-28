Usage Guide
===========

Overview
--------
The DTCC Python module makes it simple to download, process, and view city
data. In essence, you first import the module, then download or load data from
files, process the data (e.g. filtering, building meshes, or computing
attributes), and finally visualize or export the results. This guide will help
novice users get started quickly.

Importing the Module
--------------------
To begin using DTCC, simply import it as follows:

.. code-block:: python

    import dtcc

Downloading Data
----------------
DTCC provides functions to download various types of data such as point clouds,
building footprints, and road networks. For example, to download point cloud data
and building footprints for a given area, you can define the bounds and call the
appropriate functions:

.. code-block:: python

    # Define bounds (a residential area in Helsingborg)
    h = 2000.0
    bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

    # Download point cloud and building footprints
    pointcloud = dtcc.download_pointcloud(bounds=bounds)
    buildings = dtcc.download_footprints(bounds=bounds)

Loading Data from File
----------------------
In addition to downloading, DTCC allows you to load data from files. For example,
to load a CityJSON file and build a city mesh, you might do the following:

.. code-block:: python

    from urllib.request import urlretrieve
    import dtcc

    # Download example CityJSON file
    url = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/DenHaag_01.city.json"
    urlretrieve(url=url, filename="city.json")

    # Load city model from CityJSON file
    city = dtcc.load_city("city.json")

Processing Data
---------------
Once the data is downloaded or loaded, you can process it. Typical processing
steps include cleaning the data, filtering out outliers, and constructing
geometries. For example:

.. code-block:: python

    # Remove global outliers from the point cloud
    pointcloud = pointcloud.remove_global_outliers(3.0)

    # Build a terrain raster and mesh from the point cloud
    raster = dtcc.builder.build_terrain_raster(pointcloud, cell_size=5,
                                               ground_only=True)
    mesh = dtcc.builder.build_terrain_mesh(raster)

    # Extract roof points and compute building heights
    buildings = dtcc.extract_roof_points(buildings, pointcloud)
    buildings = dtcc.compute_building_heights(buildings, raster, overwrite=True)

Viewing and Exporting Data
--------------------------
After processing, DTCC makes it easy to visualize the results. Whether you are
viewing a complete city model, a terrain mesh, or a point cloud, each object
includes a ``view()`` method. For example:

.. code-block:: python

    # Create a city and add the processed buildings and terrain
    city = dtcc.City()
    city.add_buildings(buildings)
    city.add_terrain(raster)
    city.add_terrain(mesh)

    # Visualize the city model
    city.view()

For more detailed documentation and further examples, please refer to
the :ref:`API Reference` and :ref:`Demos`.
