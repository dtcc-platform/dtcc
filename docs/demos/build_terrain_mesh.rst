Demo: Build Terrain Mesh
========================

This demo illustrates how to build a terrain mesh from a point cloud.

To run the demo, type::

    $ python build_terrain_mesh.py

Purpose
-------
This demo demonstrates how to download point cloud data for a specified area,
process the data by removing global outliers, and build a terrain mesh from the
processed point cloud. Finally, the resulting terrain mesh is visualized.

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
   Remove global outliers from the point cloud to filter out noise and improve
   the quality of the mesh.

   .. code:: python

       pointcloud = pointcloud.remove_global_outliers(3.0)

4. **Build Terrain Mesh:**
   Construct a terrain mesh from the processed point cloud. The
   ``build_terrain_mesh`` function allows you to specify parameters such as maximum
   mesh size, minimum mesh angle, and smoothing factor.

   .. code:: python

       mesh = dtcc.build_terrain_mesh(
           pointcloud,
           max_mesh_size=10,
           min_mesh_angle=25,
           smoothing=3,
       )

5. **Visualize the Mesh:**
   View the generated terrain mesh using the ``view()`` method.

   .. code:: python

       mesh.view()

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/build_terrain_mesh.py
   :language: python
   :linenos:
