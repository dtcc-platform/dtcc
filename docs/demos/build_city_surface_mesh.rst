Demo: Build City Surface Mesh
==============================

This demo illustrates how to generate a surface mesh for a city directly from point cloud and footprint data using the City helper.

To run the demo, type::

    $ python build_city_surface_mesh.py

Purpose
-------
This demo demonstrates the complete workflow for acquiring the required input data, estimating building heights from a point cloud, and generating a city-scale surface mesh that can be visualized in the built-in 3D viewer. 
Starting from the constructed city model, a meshing directive in the form of a Level of Detail (LOD) specification can be assigned to each building and rendered accordingly. LoD0 buildings may be represented either as flat platforms or as voids carved into the terrain mesh, depending on the selected configuration.

Step-by-step
------------

1. **Create the City and Bounds:**
   Instantiate a city, define the horizontal extent (2000 m square around Helsingborg) and set vertical limits so downloads are clipped in height.

   .. code:: python

       city = dtcc.City()
       h = 2000.0
       bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h, 0, 200)
       city.bounds = bounds

2. **Download Data:**
   Use the city convenience methods to download point cloud and building footprints within the bounds, filtering the point cloud on the z-range.

   .. code:: python

       city.download_pointcloud(bounds=bounds, filter_on_z_bounds=True)
       city.download_footprints(bounds=bounds)

3. **Estimate Building Heights:**
   Derive building heights from the sampled point cloud.

   .. code:: python

       city.building_heights_from_pointcloud()

4. **Build the Surface Mesh:**
   Generate a surface mesh for the city based on the footprints and heights, using a meshing dirctive for each building.

   .. code:: python

        lod = [dtcc.model.GeometryType.LOD1 for _ in city.buildings]
        surface_mesh = city.build_surface_mesh(lod=lod,
                                       treat_lod0_as_holes= False)

5. **Visualize:**
   Inspect the resulting mesh in the viewer.

   .. code:: python

       surface_mesh.view()

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/build_city_surface_mesh.py
   :language: python
   :linenos:
