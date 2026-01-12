Demo: Build City Volume Mesh
============================

This demo illustrates how to generate a tetrahedral volume mesh for a city from point cloud and footprint data.

To run the demo, type::

    $ python build_city_volume_mesh.py

Purpose
-------
This demo demonstrates preparing terrain and building data, assembling a city model, and meshing it into a volumetric representation with configurable element size and domain height.

Step-by-step
------------

1. **Define Bounds:**
   Set a smaller residential area for meshing.

   .. code:: python

       h = 500.0
       bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

2. **Download Data:**
   Retrieve the point cloud and building footprints within the bounds.

   .. code:: python

       pointcloud = dtcc.download_pointcloud(bounds=bounds)
       buildings = dtcc.download_footprints(bounds=bounds)

3. **Clean the Point Cloud:**
   Remove global outliers to improve the quality of the raster and heights.

   .. code:: python

       pointcloud = pointcloud.remove_global_outliers(3.0)

4. **Build Terrain Raster:**
   Generate a ground raster for subsequent height calculations.

   .. code:: python

       raster = dtcc.build_terrain_raster(pointcloud, cell_size=2, radius=3,
                                          ground_only=True)

5. **Extract Roof Points and Heights:**
   Compute building heights relative to the terrain raster.

   .. code:: python

       buildings = dtcc.extract_roof_points(buildings, pointcloud)
       buildings = dtcc.compute_building_heights(buildings, raster, overwrite=True)

6. **Assemble the City:**
   Create the city object and add terrain plus buildings, trimming any outside the raster.

   .. code:: python

       city = dtcc.City()
       city.add_terrain(raster)
       city.add_buildings(buildings, remove_outside_terrain=True)

7. **Build the Volume Mesh:**
   Create a volumetric mesh with the chosen element size and domain height. Set ``boundary_face_markers=True`` to keep boundary faces and markers.

   .. code:: python

       volume_mesh = dtcc.build_city_volume_mesh(
           city,
           max_mesh_size=10.0,
           domain_height=80.0,
           boundary_face_markers=True,
       )

8. **Visualize:**
   View the resulting mesh in the viewer.

   .. code:: python

       volume_mesh.view()

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/build_city_volume_mesh.py
   :language: python
   :linenos:
