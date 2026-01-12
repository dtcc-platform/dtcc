Demo: Create Tiled City Mesh
============================

This demo illustrates how to create a surface mesh for a city and split it into printable tiles.

To run the demo, type::

    $ python create_tiled_city_mesh.py

Purpose
-------
This demo demonstrates downloading data, generating a surface mesh, tiling it into manageable chunks, and exporting each tile as an STL file.

Step-by-step
------------

1. **Set Up the City and Bounds:**
   Define the study area (1000 m square with z-range 0-200) and attach it to the city.

   .. code:: python

       city = City()
       h = 1000.0
       bounds = Bounds(319891, 6399790, 319891 + h, 6399790 + h, 0, 200)
       city.bounds = bounds

2. **Download Data:**
   Retrieve point cloud data clipped to the z-bounds and the matching building footprints.

   .. code:: python

       city.download_pointcloud(filter_on_z_bounds=True)
       city.download_footprints()

3. **Compute Building Heights:**
   Estimate building heights directly from the point cloud.

   .. code:: python

       city.building_heights_from_pointcloud()

4. **Build the Surface Mesh:**
   Create a city surface mesh from the footprints and heights.

   .. code:: python

       surface_mesh = city.build_surface_mesh()

5. **Normalize and Offset:**
   Move the mesh to the origin and lift it 1 m above ground so tiles extrude cleanly.

   .. code:: python

       surface_mesh.offset_to_origin()
       surface_mesh.offset([0, 0, 1])

6. **Tile the Mesh:**
   Split the mesh into 250 m tiles and report timing.

   .. code:: python

       tiles = surface_mesh.tile(tile_size=250, progress=True)

7. **Prepare Printable Solids:**
   Convert tiles to printable solids and create an output directory.

   .. code:: python

       print_tiles = [t.create_printable_solid() for t in tiles]
       outdir = Path("tiled_city_meshes")
       outdir.mkdir(exist_ok=True, parents=True)

8. **Export the Tiles:**
   Save each tile as an STL file.

   .. code:: python

       for i, t in enumerate(print_tiles):
           t.save(outdir / f"tiled_city_{i}.stl")

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/create_tiled_city_mesh.py
   :language: python
   :linenos:
