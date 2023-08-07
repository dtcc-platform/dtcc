Module dtcc
===========

Functions
---------

    
`build(parameters: dict = None) ‑> None`
:   Build city and city meshes.
    
    This function reads data from the specified data directory
    and builds a city and its corresponding meshes. The same
    thing can be accomplished by calling the individual build_*
    functions, but this function is provided as a convenience
    and takes care of loading and saving data to files.

    
`build_city(city: dtcc_model.city.City, point_cloud: dtcc_model.pointcloud.PointCloud, bounds: dtcc_model.geometry.Bounds, parameters: dict = None) ‑> dtcc_model.city.City`
:   Build city from building footprints.
    
    Developer note: Consider introducing a new class named Footprints
    so that a city can be built from footprints and point cloud data.
    It is somewhat strange that the input to this function is a city.

    
`build_mesh(city: dtcc_model.city.City, parameters: dict = None) ‑> Tuple[dtcc_model.meshes.Mesh, List[dtcc_model.meshes.Mesh]]`
:   Build mesh for city.
    
    This function builds a mesh for the city, returning two different
    meshes: one for the ground and one for the buildings.

    
`build_volume_mesh(city: dtcc_model.city.City, parameters: dict = None) ‑> Tuple[dtcc_model.meshes.VolumeMesh, dtcc_model.meshes.Mesh]`
:   Build volume mesh for city.
    
    This function builds a boundary conforming volume mesh for the city,
    returning both the volume mesh and its corresponding  boundary mesh.

    
`load_city(filename, uuid_field='id', height_field='', area_filter=None, bounds=None, min_edge_distance=2.0)`
:   

    
`load_footprints(filename, uuid_field='id', height_field='', area_filter=None, bounds=None, min_edge_distance=2.0)`
:   

    
`load_landuse(filename, landuse_field='DETALJTYP', landuse_datasource=LanduseDatasource.LM, landuse_mapping_fn=None)`
:   

    
`load_mesh(path)`
:   

    
`load_pointcloud(path, points_only=False, points_classification_only=False, delimiter=',', bounds=None)`
:   

    
`load_raster(path, delimiter=',')`
:   

    
`load_roadnetwork(road_network_file, type_field='KATEGORI', name_field='NAMN', road_datasource: dtcc_io.roadnetwork.RoadDatasource = RoadDatasource.LM, road_attribute_mapping_fn: Callable[[str], Tuple[dtcc_model.roadnetwork.RoadType, bool, bool]] = None, simplify: float = 0) ‑> dtcc_model.roadnetwork.RoadNetwork`
:   

    
`save_city(city, filename)`
:   

    
`save_footprints(city, filename)`
:   

    
`save_mesh(mesh, path)`
:   

    
`save_pointcloud(pointcloud, outfile)`
:   

    
`save_raster(raster, path)`
:   

    
`save_roadnetwork(road_network: dtcc_model.roadnetwork.RoadNetwork, out_file)`
:   

    
`view_city(cm, return_html=False, show_in_browser=False)`
:   

    
`view_mesh(mesh: dtcc_model.meshes.Mesh, mesh_data: numpy.ndarray = None, pc: dtcc_model.pointcloud.PointCloud = None, pc_data: numpy.ndarray = None)`
:   

    
`view_pointcloud(pc: dtcc_model.pointcloud.PointCloud, mesh: dtcc_model.meshes.Mesh = None, pc_data: numpy.ndarray = None, mesh_data: numpy.ndarray = None)`
:   

Classes
-------

`Bounds(xmin: float = 0.0, ymin: float = 0.0, xmax: float = 0.0, ymax: float = 0.0)`
:   Bounds(xmin: float = 0.0, ymin: float = 0.0, xmax: float = 0.0, ymax: float = 0.0)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `xmax: float`
    :

    `xmin: float`
    :

    `ymax: float`
    :

    `ymin: float`
    :

    ### Instance variables

    `area: float`
    :

    `bndstr: str`
    :

    `east: float`
    :

    `height: float`
    :

    `north: float`
    :

    `south: float`
    :

    `tuple: tuple`
    :

    `west: float`
    :

    `width: float`
    :

    ### Methods

    `buffer(self, distance: float)`
    :

    `center(self) ‑> <property object at 0x7fd338f79850>`
    :

    `from_proto(self, pb: Union[dtcc_pb2.Bounds, bytes])`
    :

    `intersect(self, other)`
    :

    `to_proto(self) ‑> dtcc_pb2.Bounds`
    :

    `union(self, other)`
    :

`Building(uuid: str = 'NONE', footprint: shapely.geometry.polygon.Polygon = <POLYGON EMPTY>, height: float = 0, ground_level: float = 0, roofpoints: dtcc_model.pointcloud.PointCloud = <factory>, crs: str = '', error: int = 0, properties: dict = <factory>)`
:   A base representation of a singele building.
    
    Attributes:
    uuid (str): The UUID of the building.
    footprint (Polygon): The polygon representing the footprint of the building.
    height (float): The height of the building.
    ground_level (float): The ground level of base of the building.
    roofpoints (PointCloud): The point cloud representing the roof points of the building.
    crs (str): The coordinate reference system of the building.
    error (int): Encoding the errors the occured when generating 3D represention of building.
    properties (dict): Additional properties of the building.

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `crs: str`
    :

    `error: int`
    :

    `footprint: shapely.geometry.polygon.Polygon`
    :

    `ground_level: float`
    :

    `height: float`
    :

    `properties: dict`
    :

    `roofpoints: dtcc_model.pointcloud.PointCloud`
    :

    `uuid: str`
    :

    ### Instance variables

    `area`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.Building, bytes])`
    :

    `to_proto(self) ‑> dtcc_pb2.Building`
    :

`City(name: str = '', bounds: dtcc_model.geometry.Bounds = <factory>, georef: dtcc_model.geometry.Georef = <factory>, terrain: dtcc_model.raster.Raster = <factory>, buildings: List[dtcc_model.building.Building] = <factory>, landuse: List[dtcc_model.landuse.Landuse] = <factory>, roadnetwork: dtcc_model.roadnetwork.RoadNetwork = <factory>)`
:   A City is the top-level container class for city models

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `bounds: dtcc_model.geometry.Bounds`
    :

    `buildings: List[dtcc_model.building.Building]`
    :

    `georef: dtcc_model.geometry.Georef`
    :

    `landuse: List[dtcc_model.landuse.Landuse]`
    :

    `name: str`
    :

    `roadnetwork: dtcc_model.roadnetwork.RoadNetwork`
    :

    `terrain: dtcc_model.raster.Raster`
    :

    ### Instance variables

    `origin`
    :

    ### Methods

    `add_building(self, building: dtcc_model.building.Building)`
    :

    `compute_building_heights(city: dtcc_model.city.City, parameters: dict = None) ‑> dtcc_model.city.City`
    :   Compute building heights from roof points

    `compute_building_points(city, pointcloud, parameters: dict = None)`
    :

    `from_proto(self, pb: Union[dtcc_pb2.City, bytes])`
    :

    `merge_buildings(city: dtcc_model.city.City, max_distance=0.15, simplify=True, properties_merge_strategy='list') ‑> dtcc_model.city.City`
    :   Merge buildings that are close together
        args:
            city: City
            max_distance: float maximum distance between buildings
            properties_merge_strategy: str strategy for merging properties.
                Options are 'list' and 'sample'. 'list' will create a list of
                all properties for the merged building. 'sample' will pick a
                property value from a random building.
        returns:
            City

    `remove_small_buildings(city: dtcc_model.city.City, min_area=10) ‑> dtcc_model.city.City`
    :   Remove small buildings
        args:
            city: City
            min_area: float minimum area of building
        returns:
            City

    `save(city, filename)`
    :

    `simplify_buildings(city: dtcc_model.city.City, tolerance=0.1) ‑> dtcc_model.city.City`
    :   Simplify buildings
        args:
            city: City
            tolerance: float tolerance for simplification
        returns:
            City

    `summarize_buildings(city: dtcc_model.city.City, print_summary=True)`
    :

    `summarize_landuse(city: dtcc_model.city.City, print_summary=True)`
    :

    `terrain_from_pointcloud(city: dtcc_model.city.City, pc: dtcc_model.pointcloud.PointCloud, cell_size: float, window_size=3, radius=0, ground_only=True) ‑> dtcc_model.city.City`
    :   Generate a terrain model from a pointcloud
        args:
            pc: PointCloud to use for terrain
            cell_size: float cell size in meters
            window_size: int window size for interpolation
            radius: float radius for interpolation
        returns:
            City

    `to_proto(self) ‑> dtcc_pb2.City`
    :

    `view(cm, return_html=False, show_in_browser=False)`
    :

`Georef(crs: str = '', epsg: int = 0, x0: float = 0.0, y0: float = 0.0)`
:   Georef(crs: str = '', epsg: int = 0, x0: float = 0.0, y0: float = 0.0)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `crs: str`
    :

    `epsg: int`
    :

    `x0: float`
    :

    `y0: float`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.Georef, bytes])`
    :

    `to_proto(self) ‑> dtcc_pb2.Georef`
    :

`Grid(bounds: dtcc_model.geometry.Bounds = <factory>, width: int = 0, height: int = 0, xstep: float = 0.0, ystep: float = 0.0)`
:   Grid(bounds: dtcc_model.geometry.Bounds = <factory>, width: int = 0, height: int = 0, xstep: float = 0.0, ystep: float = 0.0)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `bounds: dtcc_model.geometry.Bounds`
    :

    `height: int`
    :

    `width: int`
    :

    `xstep: float`
    :

    `ystep: float`
    :

    ### Instance variables

    `num_cells: int`
    :

    `num_vertices: int`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.Mesh, bytes])`
    :

    `to_proto(self) ‑> dtcc_pb2.Mesh`
    :

`GridField(grid: dtcc_model.grid.Grid = <factory>, values: numpy.ndarray = <factory>)`
:   GridField(grid: dtcc_model.grid.Grid = <factory>, values: numpy.ndarray = <factory>)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `grid: dtcc_model.grid.Grid`
    :

    `values: numpy.ndarray`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.GridField, bytes])`
    :

    `to_proto(self) ‑> dtcc_pb2.GridField`
    :

`GridVectorField(grid: dtcc_model.grid.Grid = <factory>, values: numpy.ndarray = <factory>)`
:   GridVectorField(grid: dtcc_model.grid.Grid = <factory>, values: numpy.ndarray = <factory>)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `grid: dtcc_model.grid.Grid`
    :

    `values: numpy.ndarray`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.GridVectorField, bytes])`
    :

    `to_proto(self) ‑> dtcc_pb2.GridField`
    :

`Mesh(vertices: numpy.ndarray = <factory>, vertex_colors: numpy.ndarray = <factory>, normals: numpy.ndarray = <factory>, faces: numpy.ndarray = <factory>, face_colors: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)`
:   Mesh(vertices: numpy.ndarray = <factory>, vertex_colors: numpy.ndarray = <factory>, normals: numpy.ndarray = <factory>, faces: numpy.ndarray = <factory>, face_colors: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `face_colors: numpy.ndarray`
    :

    `faces: numpy.ndarray`
    :

    `markers: numpy.ndarray`
    :

    `normals: numpy.ndarray`
    :

    `vertex_colors: numpy.ndarray`
    :

    `vertices: numpy.ndarray`
    :

    ### Instance variables

    `num_faces: int`
    :

    `num_normals: int`
    :

    `num_vertices: int`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.Mesh, bytes])`
    :

    `save(mesh, path)`
    :

    `to_proto(self) ‑> dtcc_pb2.Mesh`
    :

    `view(mesh: dtcc_model.meshes.Mesh, mesh_data: numpy.ndarray = None, pc: dtcc_model.pointcloud.PointCloud = None, pc_data: numpy.ndarray = None)`
    :

`MeshField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)`
:   MeshField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `mesh: dtcc_model.meshes.Mesh`
    :

    `values: numpy.ndarray`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.MeshField, bytes])`
    :

    `to_proto(self) ‑> dtcc_pb2.MeshField`
    :

`MeshVectorField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)`
:   MeshVectorField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)

    ### Class variables

    `mesh: dtcc_model.meshes.Mesh`
    :

    `values: numpy.ndarray`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.MeshVectorField, bytes])`
    :

    `to_proto(self) ‑> dtcc_pb2.MeshVectorField`
    :

`PointCloud(bounds: dtcc_model.geometry.Bounds = <factory>, georef: dtcc_model.geometry.Georef = <factory>, points: numpy.ndarray = <factory>, classification: numpy.ndarray = <factory>, intensity: numpy.ndarray = <factory>, return_number: numpy.ndarray = <factory>, num_returns: numpy.ndarray = <factory>)`
:   A point cloud is a set of points with associated attributes.
    Attributes:
      bounds (Bounds): The bounds of the point cloud.
      georef (Georef): The georeference of the point cloud.
      points (np.ndarray): The points of the point cloud as (n,3) dimensional numpy array.
    
      The following attributes are as defined in the las specification:
      classification (np.ndarray): The classification of the points as (n,) dimensional numpy array.
      intensity (np.ndarray): The intensity of the points as (n,) dimensional numpy array.
      return_number (np.ndarray): The return number of the points as (n,) dimensional numpy array.
      num_returns (np.ndarray): The number of returns of the points as (n,) dimensional numpy array.

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `bounds: dtcc_model.geometry.Bounds`
    :

    `classification: numpy.ndarray`
    :

    `georef: dtcc_model.geometry.Georef`
    :

    `intensity: numpy.ndarray`
    :

    `num_returns: numpy.ndarray`
    :

    `points: numpy.ndarray`
    :

    `return_number: numpy.ndarray`
    :

    ### Methods

    `calculate_bounds(self)`
    :   Calculate the bounds of the point cloud and update the bounds attribute.

    `classification_filter(pc: dtcc_model.pointcloud.PointCloud, classes: List[int], keep: bool = False)`
    :   Remove points from a pointcloud based on their classification.
        @param pc: PointCloud
        @param classes: List of classes to remove
        @param keep: If True, keep only the specified classes

    `from_proto(self, pb: Union[dtcc_pb2.PointCloud, bytes])`
    :

    `merge(self, other)`
    :   Merge another point cloud into this point cloud.

    `rasterize(pc: dtcc_model.pointcloud.PointCloud, cell_size: float, bounds: dtcc_model.geometry.Bounds = None, window_size: int = 3, radius: float = 0, ground_only: bool = True) ‑> dtcc_model.raster.Raster`
    :   Rasterize a pointcloud

    `remove_global_outliers(pc: dtcc_model.pointcloud.PointCloud, margin: float)`
    :   Remove outliers from a pointcloud using a global margin.

    `remove_points(self, indices: numpy.ndarray)`
    :   Remove points from the point cloud using the given indices.

    `save(pointcloud, outfile)`
    :

    `to_proto(self) ‑> dtcc_pb2.PointCloud`
    :

    `used_classifications(self) ‑> set`
    :

    `view(pc: dtcc_model.pointcloud.PointCloud, mesh: dtcc_model.meshes.Mesh = None, pc_data: numpy.ndarray = None, mesh_data: numpy.ndarray = None)`
    :

`Raster(data: numpy.ndarray = <factory>, georef: affine.Affine = <factory>, nodata: float = nan, crs: str = '')`
:   A georeferenced n-dimensional raster of values.
    data is a numpy array of shape (height, width, channels) or (height, width)
    if channels is 1.

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `crs: str`
    :

    `data: numpy.ndarray`
    :

    `georef: affine.Affine`
    :

    `nodata: float`
    :

    ### Instance variables

    `bounds`
    :

    `cell_size`
    :

    `channels`
    :

    `height`
    :

    `shape`
    :

    `width`
    :

    ### Methods

    `fill_holes(raster: dtcc_model.raster.Raster)`
    :   Fill nodata holes in a raster using the nearest neighbour

    `from_proto(self, pb: Union[dtcc_pb2.Raster, bytes])`
    :

    `get_value(self, x: float, y: float)`
    :   Get the value at the given coordinate

    `resample(raster: dtcc_model.raster.Raster, cell_size=None, scale=None, method='bilinear')`
    :

    `save(raster, path)`
    :

    `stats(raster: dtcc_model.raster.Raster, polygons: Union[shapely.geometry.polygon.Polygon, List[shapely.geometry.polygon.Polygon]], stats=['mean'])`
    :   Compute statistics for a raster within a polygon.
        Args:
            raster: A Raster object.
            polygons: A Polygon or a list of Polygons.
            stats: A list of statistics to compute. Supported statistics are:
            ['count', 'min', 'max', 'mean', 'median', 'majority', 'minority', 'unique',  'sum', 'std', 'var', 'percentile_X' (where X is a number between 0 and 100)]

    `to_proto(self) ‑> dtcc_pb2.Raster`
    :

`RoadNetwork(roads: List[dtcc_model.roadnetwork.Road] = <factory>, vertices: numpy.ndarray = <factory>, georef: dtcc_model.geometry.Georef = <factory>)`
:   RoadNetwork(roads: List[dtcc_model.roadnetwork.Road] = <factory>, vertices: numpy.ndarray = <factory>, georef: dtcc_model.geometry.Georef = <factory>)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `georef: dtcc_model.geometry.Georef`
    :

    `roads: List[dtcc_model.roadnetwork.Road]`
    :

    `vertices: numpy.ndarray`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.RoadNetwork, bytes])`
    :

    `save(road_network: dtcc_model.roadnetwork.RoadNetwork, out_file)`
    :

    `to_proto(self) ‑> dtcc_pb2.RoadNetwork`
    :

`VolumeMesh(vertices: numpy.ndarray = <factory>, cells: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)`
:   VolumeMesh(vertices: numpy.ndarray = <factory>, cells: numpy.ndarray = <factory>, markers: numpy.ndarray = <factory>)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `cells: numpy.ndarray`
    :

    `markers: numpy.ndarray`
    :

    `vertices: numpy.ndarray`
    :

    ### Instance variables

    `num_cells: int`
    :

    `num_vertices: int`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.VolumeMesh, bytes])`
    :

    `save(mesh, path)`
    :

    `to_proto(self) ‑> dtcc_pb2.Mesh`
    :

`VolumeMeshField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)`
:   VolumeMeshField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `mesh: dtcc_model.meshes.Mesh`
    :

    `values: numpy.ndarray`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.VolumeMeshField, bytes])`
    :

    `to_proto(self) ‑> dtcc_pb2.VolumeMeshField`
    :

`VolumeMeshVectorField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)`
:   VolumeMeshVectorField(mesh: dtcc_model.meshes.Mesh = <factory>, values: numpy.ndarray = <factory>)

    ### Ancestors (in MRO)

    * dtcc_model.model.DTCCModel
    * abc.ABC

    ### Class variables

    `mesh: dtcc_model.meshes.Mesh`
    :

    `values: numpy.ndarray`
    :

    ### Methods

    `from_proto(self, pb: Union[dtcc_pb2.VolumeMeshVectorField, bytes])`
    :

    `to_proto(self) ‑> dtcc_pb2.VolumeMeshVectorField`
    :
