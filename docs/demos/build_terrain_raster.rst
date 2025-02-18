Demo: Build Terrain Raster
==========================

This demo illustrates how to build a terrain raster from a point cloud.

To run the demo, type::

    $ python build_terrain_raster.py

Purpose
-------
This demo demonstrates how to download a point cloud for a specified area,
process the point cloud by removing global outliers, build a terrain raster from
the processed data, and finally visualize the resulting raster.

Step-by-step
------------

1. **Define Bounds:**
   Specify the spatial bounds for a residential area in Helsingborg by setting a
   height/width value (here, 2000.0 units).

   .. code:: python

       h = 2000.0
       bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

2. **Download Point Cloud:**
   Retrieve the point cloud data (lidar) for the defined bounds using the
   ``download_pointcloud`` function.

   .. code:: python

       pointcloud = dtcc.download_pointcloud(bounds=bounds)

3. **Process Data:**
   Remove global outliers from the point cloud to filter out noise.

   .. code:: python

       pointcloud = pointcloud.remove_global_outliers(3.0)

4. **Build Terrain Raster:**
   Construct a terrain raster from the processed point cloud. The
   ``build_terrain_raster`` function uses a specified cell size to create a grid
   representation of the terrain.

   .. code:: python

       raster = dtcc.build_terrain_raster(pointcloud, cell_size=10)

5. **Visualize the Raster:**
   View the generated terrain raster using the ``view()`` method.

   .. code:: python

       raster.view()

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/build_terrain_raster.py
   :language: python
   :linenos:
