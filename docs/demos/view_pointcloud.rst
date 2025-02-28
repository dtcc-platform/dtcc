Demo: View Point Cloud
======================

This demo illustrates how to download and view a point cloud.

To run the demo, type::

    $ python view_pointcloud.py


Purpose
-------

This demo demonstrates how to download point cloud data within a specified
bounding box and visualize it. The visualization colors the point cloud based
on the z-coordinate, making it easier to see elevation variations.

Step-by-step
------------

1. **Define Bounds:**
   Specify the spatial bounds for a residential area in Helsingborg by setting a
   width/height value (here, 2000.0 units).

   .. code:: python

       h = 2000.0
       bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

2. **Download the Point Cloud:**
   Retrieve the point cloud data (lidar) for the defined bounds using the
   ``download_pointcloud`` function.

   .. code:: python

       pointcloud = dtcc.download_pointcloud(bounds=bounds)

3. **Visualize the Point Cloud:**
   Extract the z-coordinate values from the point cloud and use these as color
   data when visualizing the point cloud via the ``view()`` method.

   .. code:: python

       color_data = pointcloud.points[:, 2]
       pointcloud.view(data=color_data)

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/view_pointcloud.py
   :language: python
   :linenos:
