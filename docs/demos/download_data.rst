Demo: Download Data
===================

This demo can be found in the `demos directory
<https://github.com/dtcc-platform/dtcc/tree/develop/demos>`_. To run the demo,
type::

    $ python download_data.py

Purpose
-------

This demo illustrates how to download data using different providers.
It covers downloading point cloud (lidar) data, building footprint data from
both the default (DTCC) provider and the OSM provider, as well as road network
data using the OSM provider. Finally, it demonstrates how to clear the cache of
downloaded data.

Step-by-step
------------

1. **Import the Module**

   Begin by importing the DTCC package.

   .. code:: python

       import dtcc

2. **Define the Data Bounds**

   Define the spatial bounds for a residential area in Helsingborg. Here, we set
   the dimensions by specifying a height (and width) of 2000.0 units.

   .. code:: python

       h = 2000.0
       bounds = dtcc.Bounds(319891, 6399790, 319891 + h, 6399790 + h)

3. **Download the Data**

   - **Point Cloud Data:**
     Download the lidar point cloud data within the specified bounds using the
     default provider (DTCC).

     .. code:: python

         pointcloud = dtcc.download_pointcloud(bounds=bounds)

   - **Footprint Data (DTCC Provider):**
     Download building footprint data using the default DTCC provider.

     .. code:: python

         footprints_dtcc = dtcc.download_footprints(bounds=bounds)

   - **Footprint Data (OSM Provider):**
     Download building footprint data from the OSM provider by specifying the
     provider parameter.

     .. code:: python

         footprints_osm = dtcc.download_footprints(bounds=bounds, provider="OSM")

   - **Road Network Data:**
     Download road network data using the OSM provider.

     .. code:: python

         roadnetwork_osm = dtcc.download_roadnetwork(bounds=bounds, provider="OSM")

4. **Clear the Download Cache**

   Finally, clear the cache of downloaded data.

   .. code:: python

       dtcc.empty_cache()

Complete Code
-------------
The complete code for this demo is shown below.

.. literalinclude:: ../../demos/download_data.py
   :language: python
   :linenos:
