Data Classes
============

Overview
--------

The DTCC Data Model is implemented as
`Python dataclasses <https://docs.python.org/3/library/dataclasses.html>`_ within the
DTCC Python package. In addition, the model is implemented in
`Protobuf <https://protobuf.dev/>`_ to facilitate data exchange over the web and across
different programming languages.

Objects
-------

Base class fo all city objects:

+------------------------+-------------------------------------------------+
| **Class**              | Description                                     |
+========================+=================================================+
| :class:`~dtcc.Object`  | Base class for all city objects.                |
+------------------------+-------------------------------------------------+

Specific city object classes:

+----------------------------+---------------------------------------------------------+
| **Class**                  | Description                                             |
+============================+=========================================================+
| :class:`~dtcc.Building`    | Represents a building in a city.                        |
+----------------------------+---------------------------------------------------------+
| :class:`~dtcc.BuildingPart`| Represents a component part of a building.              |
+----------------------------+---------------------------------------------------------+
| :class:`~dtcc.City`        | Top-level container representing a city model.          |
+----------------------------+---------------------------------------------------------+
| :class:`~dtcc.CityObject`  | Generic object for miscellaneous city elements.         |
+----------------------------+---------------------------------------------------------+
| :class:`~dtcc.Landuse`     | Represents land use classifications.                    |
+----------------------------+---------------------------------------------------------+
| :class:`~dtcc.RoadNetwork` | Represents a network of roads.                          |
+----------------------------+---------------------------------------------------------+
| :class:`~dtcc.Terrain`     | Represents the terrain or ground in a city.             |
+----------------------------+---------------------------------------------------------+



Geometries
----------

Base class and utility classes:

+--------------------------+----------------------------------------------------+
| **Class**                | Description                                        |
+==========================+====================================================+
| :class:`~dtcc.Geometry`  | Base class for all geometry representations.       |
+--------------------------+----------------------------------------------------+
| :class:`~dtcc.Bounds`    | Represents spatial boundaries and dimensions.      |
+--------------------------+----------------------------------------------------+
| :class:`~dtcc.Transform` | Represents an affine transformation.               |
+--------------------------+----------------------------------------------------+


Specific geometry classes:

+--------------------------------+----------------------------------------------------+
| **Class**                      | Description                                        |
+================================+====================================================+
| :class:`~dtcc.Grid`            | Structured 2D grid representation.                 |
+--------------------------------+----------------------------------------------------+
| :class:`~dtcc.LineString`      | Represents a line defined by a sequence of points. |
+--------------------------------+----------------------------------------------------+
| :class:`~dtcc.Mesh`            | Unstructured triangular mesh representation.       |
+--------------------------------+----------------------------------------------------+
| :class:`~dtcc.MultiLineString` | Composite of multiple line strings.                |
+--------------------------------+----------------------------------------------------+
| :class:`~dtcc.MultiSurface`    | Composite of multiple surface geometries.          |
+--------------------------------+----------------------------------------------------+
| :class:`~dtcc.PointCloud`      | Collection of points in 3D space.                  |
+--------------------------------+----------------------------------------------------+
| :class:`~dtcc.Polygon`         | Represents a polygon, potentially with holes.      |
+--------------------------------+----------------------------------------------------+
| :class:`~dtcc.Surface`         | Represents a planar surface in 3D.                 |
+--------------------------------+----------------------------------------------------+
| :class:`~dtcc.VolumeGrid`      | Structured 3D grid (hexahedral) representation.    |
+--------------------------------+----------------------------------------------------+
| :class:`~dtcc.VolumeMesh`      | Unstructured tetrahedral mesh representation.      |
+--------------------------------+----------------------------------------------------+


Values
------

+-----------------------+-----------------------------------------------------+
| **Class**             | Description                                         |
+=======================+=====================================================+
| :class:`~dtcc.Field`  | Represents scalar or vector fields on geometries.   |
+-----------------------+-----------------------------------------------------+
| :class:`~dtcc.Raster` | Represents grid-based raster data with georeference.|
+-----------------------+-----------------------------------------------------+


For more detailed documentation, please refer to the generated API reference pages.
