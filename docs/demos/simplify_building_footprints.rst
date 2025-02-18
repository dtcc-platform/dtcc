Demo: Simplify Building Footprints
===================================

This demo demonstrates how to simplify and process building footprints. It
covers downloading point cloud and building footprint data, removing outliers,
building a terrain raster, extracting roof points, computing building heights,
and then simplifying and splitting the building footprints for a cleaner city
model.

To run the demo, type::

    $ python simplify_building_footprints.py

Purpose
-------
This demo illustrates an end-to-end workflow for processing building footprints.
It demonstrates how to:
- Download point cloud and building footprint data.
- Process the point cloud by removing outliers.
- Build a terrain raster from the point cloud.
- Extract roof points and compute building heights.
- Simplify building footprints through merging, simplification, and clearance
  fixing.
- Optionally split footprint walls based on building height.
- Assemble a city model and visualize the result.

Step-by-step
------------

1. **Define Bounds:**
   Specify the spatial bounds for a residential area in Helsingborg by setting a
   height/width value (here, 2000.0 units).

   .. code:: python

       h = 2000.0
       bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

2. **Download Data:**
   Retrieve the point cloud and building footprint data within the defined bounds.

   .. code:: python

       pointcloud = dtcc.download_pointcloud(bounds=bounds)
       buildings = dtcc.download_footprints(bounds=bounds)

3. **Process the Point Cloud:**
   Remove global outliers from the point cloud to improve data quality.

   .. code:: python

       pointcloud = pointcloud.remove_global_outliers(3.0)

4. **Build Terrain Raster:**
   Create a terrain raster from the processed point cloud. Parameters such as
   cell size, radius, and ground filtering are specified.

   .. code:: python

       raster = dtcc.build_terrain_raster(pointcloud, cell_size=2, radius=3,
                                          ground_only=True)

5. **Extract Roof Points and Compute Building Heights:**
   Process the building footprints to extract roof points and compute building
   heights based on the terrain raster.

   .. code:: python

       buildings = dtcc.extract_roof_points(buildings, pointcloud)
       buildings = dtcc.compute_building_heights(buildings, raster, overwrite=True)

6. **Simplify Building Footprints:**
   Merge, simplify, and fix clearances in the building footprints to clean up
   the data.

   .. code:: python

       buildings = dtcc.merge_building_footprints(buildings, max_distance=0.5,
                                                  min_area=10)
       buildings = dtcc.simplify_building_footprints(buildings, tolerance=0.25)
       buildings = dtcc.fix_building_footprint_clearance(buildings, 0.5)

7. **Split Footprint Walls:**
   Optionally split building footprint walls using the building heights to
   determine maximum wall length.

   .. code:: python

       max_wall_length = [building.height for building in buildings]
       buildings = dtcc.split_footprint_walls(buildings, max_wall_length=max_wall_length)

8. **Create and Visualize the City Model:**
   Create a city object, add the processed building footprints, and visualize the
   resulting city model.

   .. code:: python

       city = dtcc.City()
       city.add_buildings(buildings)
       city.view()

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/simplify_building_footprints.py
   :language: python
   :linenos:
