Demo: Build City Mesh from CityJSON
====================================

This demo illustrates how to build a mesh for a CityJSON city model.

To run the demo, type::

    $ python build_city_mesh_from_cityjson.py

Purpose
-------
This demo demonstrates how to download a CityJSON file from an external URL,
load the city model from the file using DTCC, build a city mesh at a specified
level of detail (LOD2 in this case), and visualize the resulting mesh.

Step-by-step
------------

1. **Download CityJSON File:**
   Retrieve the CityJSON file from a specified URL and save it to a temporary file.
   This file contains the city model data in the CityJSON format.

   .. code:: python

      url = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/3-20-DELFSHAVEN.city.json"
      temp_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
      urlretrieve(url=url, filename=temp_path.name)

2. **Load City Model:**
   Load the city model from the downloaded CityJSON file using the ``load_city``
   function provided by DTCC.

   .. code:: python

       import dtcc
       city = dtcc.load_city(temp_path.name)

3. **Add terrain to the city model**
   If the model doesn't have a terrain, add a flat terrain to the city model with a buffer of 10 meters.

   .. code:: python

       if not city.has_terrain():
          city.add_flat_terrain(buffer=10)

4. **Build City Mesh:**
   Generate a city mesh from the loaded city model. Here, the mesh is built at
   level of detail LOD1.

   .. code:: python

       mesh = dtcc.build_city_mesh(city, dtcc.GeometryType.LOD1)

5. **Visualize the Mesh:**
   View the generated city mesh using the ``view()`` method.

   .. code:: python

       mesh.view()

6. **Delete Temporary File:**
   Clean up by deleting the temporary file.

   .. code:: python

       os.unlink(temp_path.name)

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/build_city_mesh_from_cityjson.py
   :language: python
   :linenos:
