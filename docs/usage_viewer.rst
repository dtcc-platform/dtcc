Visualizing data
================

The DTCC platform provides an integrated viewer which has the capability
to display large quatities of geometry, including meshes and point clouds.

To visualize a point cloud colored by the x-position of the points:

.. code:: python

    from dtcc import *
    filename = 'data/helsingborg-residential-2022/pointcloud.las'
    pc = load_pointcloud(filename)
    color_data = pc.points[:,0]
    pc.view(pc_data = color_data)


To build a city from raw data and view its the boundary mesh together with the pointcloud:

.. code:: python

    from dtcc import *

    # Build a mesh from raw data
    data_directory = Path("../data/dtcc-demo-data/helsingborg-residential-2022")
    p = parameters.default()
    p["data_directory"] = data_directory
    build(p)

    # The path for the building footprints data
    buildings_path = data_directory / "footprints.shp"

    # Path to the folder where the pointcloud file / files is located
    pointcloud_path = data_directory

    origin, bounds = calculate_bounds(buildings_path, pointcloud_path, p)
    city = load_city(buildings_path, bounds=bounds)
    pointcloud = load_pointcloud(pointcloud_path, bounds=bounds)

    # Build a city
    city = build_city(city, pointcloud, bounds, p)

    # From the city build meshes
    volume_mesh, boundary_mesh = build_volume_mesh(city)

    # View the boundary mesh together with the point cloud.
    boundary_mesh.view(pc=pointcloud)


To visualise an arbitrary multiple of meshes and pointclouds a Scene object is created
to which the data is appended. This example shows how to build a city from raw data
and how to visualise the ground mesh, the building mesh and the combined boundary mesh
together with the pointcloud that was used as input. 

.. code:: python

    from dtcc import *

    # Build a mesh from raw data
    data_directory = Path("../data/dtcc-demo-data/helsingborg-residential-2022")
    p = parameters.default()
    p["data_directory"] = data_directory
    build(p)

    # The path for the building footprints data
    buildings_path = data_directory / "footprints.shp"

    # Path to the folder where the pointcloud file / files is located
    pointcloud_path = data_directory

    origin, bounds = calculate_bounds(buildings_path, pointcloud_path, p)
    city = load_city(buildings_path, bounds=bounds)
    pointcloud = load_pointcloud(pointcloud_path, bounds=bounds)

    # Build a city
    city = build_city(city, pointcloud, bounds, p)

    # From the city build meshes
    ground_mesh, building_mesh = build_mesh(city, p)

    # Create a scene and window.
    scene = Scene()
    window = Window(1200, 800)
    
    # Create MeshData objects which bundel a mesh and appended data or colors
    # To provide data for coloring the keyword argument "mesh_data="" is used.
    # To provied colors directly the keyword argument "mesh_colors=" is used. 
    scene.add_mesh(MeshData("Building mesh", building_mesh))
    scene.add_mesh(MeshData("Ground mesh", ground_mesh))
    scene.add_mesh(MeshData("Boundary mesh", boundary_mesh))

    # Create PointCloudData object which bundels a pointcloud with data or colors.
    # To provide data for coloring the keyword argument "pc_data="" is used.
    # To provied colors directly the keyword argument "pc_colors=" is used. 
    scene.add_pointcloud(PointCloudData("Point cloud", pointcloud))

    # Render geometry
    window.render(scene)


Viewer controls
---------------

Once the DTCC Viewer is running and a graphics window is the viewport
navigation is done with the mouse according to:

- `Left mouse button` - Rotate the view around the camera target
- `Right mouse button` - Panning the view, thus moving the camera target
- `Scroll` - Zoom in and out at the current camera target

A GUI is also created with global controls for the whole scene under
apperance which includes things like (background color etc). Individual
GUI components are also created for each Mesh and Point Cloud that is
on display.
