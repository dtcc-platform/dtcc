Demo: Build LOD1 Buildings
==========================

This demo illustrates how to construct LOD1 building models from point cloud and footprint data and merge them into a single mesh.

To run the demo, type::

    $ python build_lod1_buildings.py

Purpose
-------
This demo shows the workflow for cleaning point cloud data, deriving terrain and building heights, generating LOD1 geometries, and exporting a unified mesh suitable for visualization or printing.

Step-by-step
------------

1. **Define Bounds:**
   Choose bounds for the study area.

   .. code:: python

       h = 2000.0
       bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

2. **Download Data:**
   Fetch the point cloud and building footprints within the bounds.

   .. code:: python

       pointcloud = dtcc.download_pointcloud(bounds=bounds)
       buildings = dtcc.download_footprints(bounds=bounds)

3. **Clean the Point Cloud:**
   Remove global outliers to improve data quality.

   .. code:: python

       pointcloud = pointcloud.remove_global_outliers(3.0)

4. **Build Terrain Raster:**
   Generate a ground raster to use for height calculations.

   .. code:: python

       raster = dtcc.builder.build_terrain_raster(pointcloud, cell_size=5,
                                                  ground_only=True)

5. **Compute Building Heights:**
   Extract roof points from the point cloud and compute per-building heights.

   .. code:: python

       buildings = dtcc.extract_roof_points(buildings, pointcloud)
       buildings = dtcc.compute_building_heights(buildings, raster, overwrite=True)

6. **Create LOD1 Buildings:**
   Build LOD1 volumes, allowing the terrain minimum to be used as a default ground height when needed.

   .. code:: python

       buildings = dtcc.builder.build_lod1_buildings(
           buildings,
           default_ground_height=raster.min,
           always_use_default_ground=False,
       )

7. **Mesh and Normalize Heights:**
   Generate meshes for each building, weld vertices, snap close points, and move the bases to ``z = 0`` for merging.

   .. code:: python

       building_meshes = [b.lod1.mesh(weld=True, snap=0.005) for b in buildings]
       for b in building_meshes:
           b.offset([0, 0, -b.bounds.zmin])

8. **Merge and View:**
   Combine individual building meshes into one and open the viewer.

   .. code:: python

       merged_mesh = dtcc.builder.meshing.merge_meshes(building_meshes)
       merged_mesh.view()

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/build_lod1_buildings.py
   :language: python
   :linenos:
