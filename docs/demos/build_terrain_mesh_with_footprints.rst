Demo: Build Terrain Mesh With Footprints
========================================

This demo illustrates how to build a terrain mesh that conforms to building
footprints.

To run the demo, type::

    $ python build_terrain_mesh_with_footprints.py

Purpose
-------
This demo demonstrates how to download point cloud data and building footprints
from the OSM provider, process and simplify the footprints, and then build a
terrain mesh with the footprints serving as subdomains. This approach allows
the mesh to better conform to the building boundaries.

Step-by-step
------------

1. **Define Bounds:**
   Specify the spatial bounds for a residential area in Helsingborg by setting a
   height/width value (here, 2000.0 units).

   .. code:: python

       h = 2000.0
       bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

2. **Download Data:**
   Retrieve the point cloud and building footprints using the appropriate
   functions. The footprints are downloaded from the OSM provider.

   .. code:: python

       pointcloud = dtcc.download_pointcloud(bounds=bounds)
       buildings = dtcc.download_footprints(bounds=bounds, provider="OSM")

3. **Process the Point Cloud:**
   Remove global outliers from the point cloud to reduce noise.

   .. code:: python

       pointcloud = pointcloud.remove_global_outliers(3.0)

4. **Process and Simplify Footprints:**
   Merge, simplify, and adjust the building footprints. These steps ensure
   that the footprints are clean and suitable for defining subdomains in the mesh.

   .. code:: python

       buildings = dtcc.merge_building_footprints(buildings, max_distance=0.5,
                                                  min_area=10)
       buildings = dtcc.simplify_building_footprints(buildings, tolerance=0.25)
       buildings = dtcc.fix_building_footprint_clearance(buildings, 0.5)

5. **Extract Footprints:**
   Extract the simplified footprints (using the LOD0 representation) from the
   processed building objects.

   .. code:: python

       footprints = [building.lod0 for building in buildings]

6. **Define Subdomain Resolutions:**
   Set subdomain resolutions, assigning different resolutions for alternate
   buildings.

   .. code:: python

       subdomain_resolution = [2.0] * len(footprints)
       subdomain_resolution[1::2] = [0.5] * len(subdomain_resolution[1::2])

7. **Build the Terrain Mesh:**
   Build the terrain mesh by supplying the point cloud, the extracted footprints
   as subdomains, and the corresponding resolution settings. Additional parameters
   such as maximum mesh size, minimum mesh angle, and smoothing factor are also
   specified.

   .. code:: python

       mesh = dtcc.build_terrain_mesh(
           pointcloud,
           subdomains=footprints,
           subdomain_resolution=subdomain_resolution,
           max_mesh_size=10,
           min_mesh_angle=25,
           smoothing=3,
       )

8. **Visualize the Mesh:**
   Display the resulting terrain mesh using the ``view()`` method.

   .. code:: python

       mesh.view()

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/build_terrain_mesh_with_footprints.py
   :language: python
   :linenos:
