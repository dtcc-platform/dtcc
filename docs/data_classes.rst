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

+----------------+---------------------------------------------------------+
| **Class**      | Description                                             |
+================+=========================================================+
| Object         | Base class for all city objects.                        |
+----------------+---------------------------------------------------------+

Specific city object classes:

+----------------+---------------------------------------------------------+
| **Class**      | Description                                             |
+================+=========================================================+
| Building       | Represents a building in a city.                        |
+----------------+---------------------------------------------------------+
| BuildingPart   | Represents a component part of a building.              |
+----------------+---------------------------------------------------------+
| City           | Top-level container representing a city model.          |
+----------------+---------------------------------------------------------+
| CityObject     | Generic object for miscellaneous city elements.         |
+----------------+---------------------------------------------------------+
| Landuse        | Represents land use classifications.                    |
+----------------+---------------------------------------------------------+
| RoadNetwork    | Represents a network of roads.                          |
+----------------+---------------------------------------------------------+
| Terrain        | Represents the terrain or ground in a city.             |
+----------------+---------------------------------------------------------+

Geometries
----------

Base class and utility classes:

+------------------+----------------------------------------------------+
| **Class**        | Description                                        |
+==================+====================================================+
| Geometry         | Base class for all geometry representations.       |
+------------------+----------------------------------------------------+
| Bounds           | Represents spatial boundaries and dimensions.      |
+------------------+----------------------------------------------------+
| Transform        | Represents an affine transformation.               |
+------------------+----------------------------------------------------+

Specific geometry classes:

+------------------+----------------------------------------------------+
| **Class**        | Description                                        |
+==================+====================================================+
| Grid             | Structured 2D grid representation.                 |
+------------------+----------------------------------------------------+
| LineString       | Represents a line defined by a sequence of points. |
+------------------+----------------------------------------------------+
| Mesh             | Unstructured triangular mesh representation.       |
+------------------+----------------------------------------------------+
| MultiLineString  | Composite of multiple line strings.                |
+------------------+----------------------------------------------------+
| MultiSurface     | Composite of multiple surface geometries.          |
+------------------+----------------------------------------------------+
| PointCloud       | Collection of points in 3D space.                  |
+------------------+----------------------------------------------------+
| Polygon          | Represents a polygon, potentially with holes.      |
+------------------+----------------------------------------------------+
| Surface          | Represents a planar surface in 3D.                 |
+------------------+----------------------------------------------------+
| VolumeGrid       | Structured 3D grid (hexahedral) representation.    |
+------------------+----------------------------------------------------+
| VolumeMesh       | Unstructured tetrahedral mesh representation.      |
+------------------+----------------------------------------------------+

Values
------

+----------+-----------------------------------------------------+
| Class    | Description                                         |
+==========+=====================================================+
| Field    | Represents scalar or vector fields on geometries.   |
+----------+-----------------------------------------------------+
| Raster   | Represents grid-based raster data with georeference.|
+----------+-----------------------------------------------------+

For more detailed documentation, please refer to the generated API reference pages.
