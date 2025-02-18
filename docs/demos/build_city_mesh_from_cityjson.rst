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
   Retrieve the CityJSON file from a specified URL. This file contains the city
   model data in the CityJSON format.

   .. code:: python

       from urllib.request import urlretrieve
       url = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/DenHaag_01.city.json"
       urlretrieve(url=url, filename="city.json")

2. **Load City Model:**
   Load the city model from the downloaded CityJSON file using the ``load_city``
   function provided by DTCC.

   .. code:: python

       import dtcc
       city = dtcc.load_city("city.json")

3. **Build City Mesh:**
   Generate a city mesh from the loaded city model. Here, the mesh is built at
   level of detail LOD2.

   .. code:: python

       mesh = dtcc.build_city_mesh(city, dtcc.GeometryType.LOD2)

4. **Visualize the Mesh:**
   View the generated city mesh using the ``view()`` method.

   .. code:: python

       mesh.view()

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/build_city_mesh_from_cityjson.py
   :language: python
   :linenos:
