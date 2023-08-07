# Summary of API for dtcc

## Modules

* `builder`
* `io`
* `model`
* `module`
* `proto`
* `viewer`
* `wrangler`

## Classes

### Bounds
Bounds(xmin: float = 0.0, ymin: float = 0.0, xmax: float = 0.0, ymax: float = 0.0)
### Building
A base representation of a singele building.

    Attributes:
    uuid (str): The UUID of the building.
    footprint (Polygon): The polygon representing the footprint of the building.
    height (float): The height of the building.
    ground_level (float): The ground level of base of the building.
    roofpoints (PointCloud): The point cloud representing the roof points of the building.
    crs (str): The coordinate reference system of the building.
    error (int): Encoding the errors the occured when generating 3D represention of building.
    properties (dict): Additional properties of the building.

    
### City
A City is the top-level container class for city models
### Georef
Georef(crs: str = '', epsg: int = 0, x0: float = 0.0, y0: float = 0.0)
### Grid
Grid(bounds: dtcc_model.geometry.Bounds = <factory>, width: int = 0, height: int = 0, xstep: float = 0.0, ystep: float = 0.0)
### GridField
GridField(grid: dtcc_model.grid.Grid = <factory>, values: numpy.ndarray = <factory>)
### GridVectorField
GridVectorField(grid: dtcc_model.grid.Grid = <factory>, values: numpy.ndarray = <factory>)
### Mesh
Mesh(vertices: numpy.ndarray = <factory>, vertex_colors: numpy.ndarray = <factory>, normals: numpy.ndarray = <factory>, faces: numpy.ndarray = <factory>, face_colors: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)
### MeshField
MeshField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)
### MeshVectorField
MeshVectorField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)
### PointCloud
A point cloud is a set of points with associated attributes.
    Attributes:
      bounds (Bounds): The bounds of the point cloud.
      georef (Georef): The georeference of the point cloud.
      points (np.ndarray): The points of the point cloud as (n,3) dimensional numpy array.

      The following attributes are as defined in the las specification:
      classification (np.ndarray): The classification of the points as (n,) dimensional numpy array.
      intensity (np.ndarray): The intensity of the points as (n,) dimensional numpy array.
      return_number (np.ndarray): The return number of the points as (n,) dimensional numpy array.
      num_returns (np.ndarray): The number of returns of the points as (n,) dimensional numpy array.


    
### Raster
A georeferenced n-dimensional raster of values.
    data is a numpy array of shape (height, width, channels) or (height, width)
    if channels is 1.
    
### RoadNetwork
RoadNetwork(roads: List[dtcc_model.roadnetwork.Road] = <factory>, vertices: numpy.ndarray = <factory>, georef: dtcc_model.geometry.Georef = <factory>)
### VolumeMesh
VolumeMesh(vertices: numpy.ndarray = <factory>, cells: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)
### VolumeMeshField
VolumeMeshField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)
### VolumeMeshVectorField
VolumeMeshVectorField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)

## Functions:

### build()

    Build city and city meshes.

    This function reads data from the specified data directory
    and builds a city and its corresponding meshes. The same
    thing can be accomplished by calling the individual build_*
    functions, but this function is provided as a convenience
    and takes care of loading and saving data to files.
    
### build_city()

    Build city from building footprints.

    Developer note: Consider introducing a new class named Footprints
    so that a city can be built from footprints and point cloud data.
    It is somewhat strange that the input to this function is a city.
    
### build_mesh()

    Build mesh for city.

    This function builds a mesh for the city, returning two different
    meshes: one for the ground and one for the buildings.
    
### build_volume_mesh()
Build volume mesh for city.

    This function builds a boundary conforming volume mesh for the city,
    returning both the volume mesh and its corresponding  boundary mesh.
    
### load_city()
None
### load_footprints()
None
### load_landuse()
None
### load_mesh()
None
### load_pointcloud()
None
### load_raster()
None
### load_roadnetwork()
None
### save_city()
None
### save_footprints()
None
### save_mesh()
None
### save_pointcloud()
None
### save_raster()
None
### save_roadnetwork()
None
### view_city()
None
### view_mesh()
None
### view_pointcloud()
None

# Summary of API for dtcc.builder

## Modules

* `_dtcc_builder`
* `builders`
* `city_methods`
* `logging`
* `model`
* `parameters`

## Classes

### City
A City is the top-level container class for city models
### PointCloud
A point cloud is a set of points with associated attributes.
    Attributes:
      bounds (Bounds): The bounds of the point cloud.
      georef (Georef): The georeference of the point cloud.
      points (np.ndarray): The points of the point cloud as (n,3) dimensional numpy array.

      The following attributes are as defined in the las specification:
      classification (np.ndarray): The classification of the points as (n,) dimensional numpy array.
      intensity (np.ndarray): The intensity of the points as (n,) dimensional numpy array.
      return_number (np.ndarray): The return number of the points as (n,) dimensional numpy array.
      num_returns (np.ndarray): The number of returns of the points as (n,) dimensional numpy array.


    

## Functions:

### build()

    Build city and city meshes.

    This function reads data from the specified data directory
    and builds a city and its corresponding meshes. The same
    thing can be accomplished by calling the individual build_*
    functions, but this function is provided as a convenience
    and takes care of loading and saving data to files.
    
### build_city()

    Build city from building footprints.

    Developer note: Consider introducing a new class named Footprints
    so that a city can be built from footprints and point cloud data.
    It is somewhat strange that the input to this function is a city.
    
### build_mesh()

    Build mesh for city.

    This function builds a mesh for the city, returning two different
    meshes: one for the ground and one for the buildings.
    
### build_volume_mesh()
Build volume mesh for city.

    This function builds a boundary conforming volume mesh for the city,
    returning both the volume mesh and its corresponding  boundary mesh.
    

# Summary of API for dtcc.io

## Modules

* `bounds`
* `city`
* `fields`
* `generic`
* `gridfield`
* `landuse`
* `logging`
* `meshes`
* `pointcloud`
* `raster`
* `roadnetwork`

## Classes

### City
A City is the top-level container class for city models
### Mesh
Mesh(vertices: numpy.ndarray = <factory>, vertex_colors: numpy.ndarray = <factory>, normals: numpy.ndarray = <factory>, faces: numpy.ndarray = <factory>, face_colors: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)
### PointCloud
A point cloud is a set of points with associated attributes.
    Attributes:
      bounds (Bounds): The bounds of the point cloud.
      georef (Georef): The georeference of the point cloud.
      points (np.ndarray): The points of the point cloud as (n,3) dimensional numpy array.

      The following attributes are as defined in the las specification:
      classification (np.ndarray): The classification of the points as (n,) dimensional numpy array.
      intensity (np.ndarray): The intensity of the points as (n,) dimensional numpy array.
      return_number (np.ndarray): The return number of the points as (n,) dimensional numpy array.
      num_returns (np.ndarray): The number of returns of the points as (n,) dimensional numpy array.


    
### Raster
A georeferenced n-dimensional raster of values.
    data is a numpy array of shape (height, width, channels) or (height, width)
    if channels is 1.
    
### RoadNetwork
RoadNetwork(roads: List[dtcc_model.roadnetwork.Road] = <factory>, vertices: numpy.ndarray = <factory>, georef: dtcc_model.geometry.Georef = <factory>)
### VolumeMesh
VolumeMesh(vertices: numpy.ndarray = <factory>, cells: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)

## Functions:

### list_field_io()
None
### list_mesh_io()
None
### load_city()
None
### load_footprints()
None
### load_gridfield()
None
### load_landuse()
None
### load_mesh()
None
### load_mesh_field()
None
### load_mesh_vector_field()
None
### load_pointcloud()
None
### load_raster()
None
### load_roadnetwork()
None
### load_volume_mesh()
None
### print_field_io()
None
### print_mesh_io()
None
### save_city()
None
### save_field()
None
### save_footprints()
None
### save_gridfield()
None
### save_mesh()
None
### save_pointcloud()
None
### save_raster()
None
### save_roadnetwork()
None

# Summary of API for dtcc.model

## Modules

* `building`
* `city`
* `dtcc_pb2`
* `geometry`
* `grid`
* `gridfields`
* `landuse`
* `meshes`
* `meshfields`
* `model`
* `pointcloud`
* `proto`
* `raster`
* `roadnetwork`
* `utils`

## Classes

### Bounds
Bounds(xmin: float = 0.0, ymin: float = 0.0, xmax: float = 0.0, ymax: float = 0.0)
### Building
A base representation of a singele building.

    Attributes:
    uuid (str): The UUID of the building.
    footprint (Polygon): The polygon representing the footprint of the building.
    height (float): The height of the building.
    ground_level (float): The ground level of base of the building.
    roofpoints (PointCloud): The point cloud representing the roof points of the building.
    crs (str): The coordinate reference system of the building.
    error (int): Encoding the errors the occured when generating 3D represention of building.
    properties (dict): Additional properties of the building.

    
### City
A City is the top-level container class for city models
### Georef
Georef(crs: str = '', epsg: int = 0, x0: float = 0.0, y0: float = 0.0)
### Grid
Grid(bounds: dtcc_model.geometry.Bounds = <factory>, width: int = 0, height: int = 0, xstep: float = 0.0, ystep: float = 0.0)
### GridField
GridField(grid: dtcc_model.grid.Grid = <factory>, values: numpy.ndarray = <factory>)
### GridVectorField
GridVectorField(grid: dtcc_model.grid.Grid = <factory>, values: numpy.ndarray = <factory>)
### Landuse
A polygon of a singele landuse area.:
    available landuse types are:
    WATER, GRASS, FOREST, FARMLAND, URBAN, INDUSTRIAL, MILITARY, ROAD, RAIL
### Mesh
Mesh(vertices: numpy.ndarray = <factory>, vertex_colors: numpy.ndarray = <factory>, normals: numpy.ndarray = <factory>, faces: numpy.ndarray = <factory>, face_colors: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)
### MeshField
MeshField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)
### MeshVectorField
MeshVectorField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)
### PointCloud
A point cloud is a set of points with associated attributes.
    Attributes:
      bounds (Bounds): The bounds of the point cloud.
      georef (Georef): The georeference of the point cloud.
      points (np.ndarray): The points of the point cloud as (n,3) dimensional numpy array.

      The following attributes are as defined in the las specification:
      classification (np.ndarray): The classification of the points as (n,) dimensional numpy array.
      intensity (np.ndarray): The intensity of the points as (n,) dimensional numpy array.
      return_number (np.ndarray): The return number of the points as (n,) dimensional numpy array.
      num_returns (np.ndarray): The number of returns of the points as (n,) dimensional numpy array.


    
### Raster
A georeferenced n-dimensional raster of values.
    data is a numpy array of shape (height, width, channels) or (height, width)
    if channels is 1.
    
### RoadNetwork
RoadNetwork(roads: List[dtcc_model.roadnetwork.Road] = <factory>, vertices: numpy.ndarray = <factory>, georef: dtcc_model.geometry.Georef = <factory>)
### RoadType
An enumeration.
### VolumeMesh
VolumeMesh(vertices: numpy.ndarray = <factory>, cells: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)
### VolumeMeshField
VolumeMeshField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)
### VolumeMeshVectorField
VolumeMeshVectorField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)

## Functions:


# Summary of API for dtcc.module

## Modules

* `citymodel`
* `colors`
* `mesh_opengl`
* `notebook_functions`
* `opengl_viewer`
* `pointcloud_opengl`
* `random_colors`
* `utils`

## Classes

### City
A City is the top-level container class for city models
### Mesh
Mesh(vertices: numpy.ndarray = <factory>, vertex_colors: numpy.ndarray = <factory>, normals: numpy.ndarray = <factory>, faces: numpy.ndarray = <factory>, face_colors: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)
### PointCloud
A point cloud is a set of points with associated attributes.
    Attributes:
      bounds (Bounds): The bounds of the point cloud.
      georef (Georef): The georeference of the point cloud.
      points (np.ndarray): The points of the point cloud as (n,3) dimensional numpy array.

      The following attributes are as defined in the las specification:
      classification (np.ndarray): The classification of the points as (n,) dimensional numpy array.
      intensity (np.ndarray): The intensity of the points as (n,) dimensional numpy array.
      return_number (np.ndarray): The return number of the points as (n,) dimensional numpy array.
      num_returns (np.ndarray): The number of returns of the points as (n,) dimensional numpy array.


    

## Functions:

### view_city()
None
### view_mesh()
None
### view_pointcloud()
None

# Summary of API for dtcc.proto

## Modules

* `_descriptor`
* `_message`
* `_reflection`
* `_symbol_database`

## Classes

### AffineTransform
None
### Bounds
None
### Building
None
### City
None
### Georef
None
### Grid
None
### GridField
None
### GridVectorField
None
### LandUse
None
### LineString
None
### LineString3D
None
### LinearRing
None
### Mesh
None
### MeshField
None
### MeshVectorField
None
### MultiPoint
None
### MultiPoint3D
None
### MultiPolygon
None
### PointCloud
None
### Polygon
None
### Raster
None
### Road
None
### RoadNetwork
None
### Vector2D
None
### Vector3D
None
### VolumeMesh
None
### VolumeMeshField
None
### VolumeMeshVectorField
None

## Functions:


# Summary of API for dtcc.viewer

## Modules

* `citymodel`
* `colors`
* `mesh_opengl`
* `notebook_functions`
* `opengl_viewer`
* `pointcloud_opengl`
* `random_colors`
* `utils`

## Classes

### City
A City is the top-level container class for city models
### Mesh
Mesh(vertices: numpy.ndarray = <factory>, vertex_colors: numpy.ndarray = <factory>, normals: numpy.ndarray = <factory>, faces: numpy.ndarray = <factory>, face_colors: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)
### PointCloud
A point cloud is a set of points with associated attributes.
    Attributes:
      bounds (Bounds): The bounds of the point cloud.
      georef (Georef): The georeference of the point cloud.
      points (np.ndarray): The points of the point cloud as (n,3) dimensional numpy array.

      The following attributes are as defined in the las specification:
      classification (np.ndarray): The classification of the points as (n,) dimensional numpy array.
      intensity (np.ndarray): The intensity of the points as (n,) dimensional numpy array.
      return_number (np.ndarray): The return number of the points as (n,) dimensional numpy array.
      num_returns (np.ndarray): The number of returns of the points as (n,) dimensional numpy array.


    

## Functions:

### view_city()
None
### view_mesh()
None
### view_pointcloud()
None

# Summary of API for dtcc.wrangler

## Modules

* `city`
* `geometry`
* `logging`
* `pointcloud`
* `raster`
* `register`

## Classes


## Functions:


