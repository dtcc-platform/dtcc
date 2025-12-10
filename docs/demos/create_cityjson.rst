Demo: Create CityJSON
=====================

This demo illustrates how to build a CityJSON city model with terrain and LOD1 buildings and save it to disk.

To run the demo, type::

    $ python create_cityjson.py

Purpose
-------
This demo walks through setting up a ``City`` with downloaded data, generating terrain and building geometry, saving the result as ``test_city.json``, and visualizing it.

Step-by-step
------------

1. **Initialize City and Bounds:**
   Create the city and set bounds for a 2000 m square around Helsingborg.

   .. code:: python

       h = 2000.0
       bounds = Bounds(319891, 6399790, 319891 + h, 6399790 + h)

       city = City()
       city.bounds = bounds

2. **Download Inputs:**
   Fetch footprints and point cloud data for the defined bounds using the city helpers.

   .. code:: python

       city.download_footprints()
       city.download_pointcloud()

3. **Build Terrain:**
   Construct a terrain raster and mesh to serve as ground for the city.

   .. code:: python

       city.build_terrain(
           cell_size=2.0,
           build_mesh=True,
           max_triangle_size=5.0,
           smoothing=3,
       )

4. **Generate LOD1 Buildings:**
   Create LOD1 building geometry based on the available footprints and heights.

   .. code:: python

       city.build_lod1_buildings()

5. **Save and View:**
   Export the city to CityJSON and visualize it.

   .. code:: python

       city.save("test_city.json")
       city.view()

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/create_cityjson.py
   :language: python
   :linenos:
