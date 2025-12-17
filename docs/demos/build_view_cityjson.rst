Demo: Build View CityJSON
=========================

This demo illustrates how to download a sample CityJSON file, enrich it with attributes, and explore it in the 3D viewer.

To run the demo, type::

    $ python build_view_cityjson.py

Purpose
-------
This demo shows how to load external CityJSON data, attach per-building metadata, and use the viewer controls to inspect attributes interactively.

Step-by-step
------------

1. **Download a CityJSON Sample:**
   Fetch a sample CityJSON file (Den Haag) to ``city.json`` using ``urlretrieve``. A second URL is provided in the script if you want to try another dataset.

   .. code:: python

       url = "https://3d.bk.tudelft.nl/opendata/cityjson/3dcities/v2.0/DenHaag_01.city.json"
       urlretrieve(url=url, filename="city.json")

2. **Load the City Model:**
   Read the CityJSON file into a ``City`` object.

   .. code:: python

       city = dtcc.load_city("city.json")

3. **Add Building Attributes:**
   Create synthetic values for construction year and number of residents and attach them to each building to explore attribute styling in the viewer.

   .. code:: python

       building_year = [1900, 1920, 1940, 1960, 1980, 2000, 2020]
       residents = np.arange(10) + 5
       for i, building in enumerate(city.buildings):
           building.attributes["number residents"] = residents[i % len(residents)]
           building.attributes["construction year"] = building_year[i % len(building_year)]

4. **View the Model:**
   Launch the viewer to inspect geometry and attributes.

   .. code:: python

       city.view()

Viewer tips
-----------
- Click buildings to inspect attributes in the data tab.
- Press ``z`` to zoom to the selected object and ``x`` to fit the full extent.
- Use the Controls -> Model -> Buildings options to color by any attribute and adjust color ranges.

Complete Code
-------------
Below is the complete code for this demo:

.. literalinclude:: ../../demos/build_view_cityjson.py
   :language: python
   :linenos:
