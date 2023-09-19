Visualizing data
================

The DTCC platform provides an integrated viewer which has the capability
to display large quantities of geometry, including meshes and point clouds.

The first example demonstrates how to visualize a point cloud colored by the x-position 
of the points:

.. code:: python

    import dtcc
    filename = '../data/dtcc-demo-data/helsingborg-residential-2022/pointcloud.las'
    pc = dtcc.io.load_pointcloud(filename)
    color_data = pc.points[:,0]
    pc.view(pc_data = color_data)

The second example demonstrates how to build a city from raw data and view the building 
mesh with three different coloring options. The first option is the default colors 
calculated from vertex z-coordinates. In the second option colors are are determined 
based on appended data. In the third option the colors as [r, g, b] values in the range 
[0, 1] are appended directly.   

.. code:: python

    from pathlib import Path
    import numpy as np
    import dtcc

    # Build a mesh from raw data
    data_directory = Path("../data/helsingborg-residential-2022")
    p = dtcc.builder.parameters.default()
    p["data_directory"] = data_directory
    dtcc.builder.build(p)

    buildings_path = data_directory / "footprints.shp"
    pointcloud_path = data_directory

    origin, bounds = dtcc.builder.calculate_bounds(buildings_path, pointcloud_path, p)
    city = dtcc.io.load_city(buildings_path, bounds=bounds)
    pointcloud = dtcc.io.load_pointcloud(pointcloud_path, bounds=bounds)

    # Build a city
    city = dtcc.builder.build_city(city, pointcloud, bounds, p)

    # From the city build meshes
    ground_mesh, building_mesh = dtcc.builder.build_mesh(city, p)

    # Toggle the viewin_option variable between 1,2,3 to try different modes of viewing.
    viewing_option = 1

    # View the building mesh with default colors
    if(viewing_option == 1): 
        building_mesh.view()

    # View the building mesh with data per vertex  
    elif viewing_option == 2:
        data = building_mesh.vertices[:, 1]

        # View the building mesh and appedn colors 
        building_mesh.view(data=data)

    # View the building mesh with an appended array of colors matching the vertex count    
    elif viewing_option == 3:
        # Normalise the data so it falls in the range [0,1]
        min = building_mesh.vertices[:, 1].min()
        max = building_mesh.vertices[:, 1].max()
        color_data = (building_mesh.vertices[:, 1] - min) / (max - min)

        # Create an np array with colors matching the number of vertices of the mesh.
        colors = np.zeros((len(building_mesh.vertices), 3))
        colors[:, 1] = color_data

        # View the building mesh and appedn colors 
        building_mesh.view(colors=colors)

The third example shows how to build a city from raw data and view its ground mesh 
together with the pointcloud:

.. code:: python

    from pathlib import Path
    import dtcc

    # Build a mesh from raw data
    data_directory = Path("../data/helsingborg-residential-2022")
    p = dtcc.builder.parameters.default()
    p["data_directory"] = data_directory
    dtcc.builder.build(p)

    buildings_path = data_directory / "footprints.shp"
    pointcloud_path = data_directory

    origin, bounds = dtcc.builder.calculate_bounds(buildings_path, pointcloud_path, p)
    city = dtcc.io.load_city(buildings_path, bounds=bounds)
    pointcloud = dtcc.io.load_pointcloud(pointcloud_path, bounds=bounds)

    # Build a city
    city = dtcc.builder.build_city(city, pointcloud, bounds, p)

    # From the city build meshes
    ground_mesh, building_mesh = dtcc.builder.build_mesh(city, p)

    # From the city build meshes
    volume_mesh, boundary_mesh = dtcc.builder.build_volume_mesh(city)

    # Remove unwanted outliers from the point cloud
    pc = pointcloud.remove_global_outliers(3)

    # View the gorund mesh togheter with the pointcloud
    ground_mesh.view(pc=pc)

    # Alternatively the pointcloud can be viewed with the mesh as agument
    # pointcloud.view(mesh=ground_mesh)

The fourth example shows how to visualise a range of meshes and/or pointclouds. A Scene 
object is then created to which meshes and point clouds are added. This example shows how 
to build a city from raw data and how to visualise the ground mesh, the building mesh
and the boundary mesh together with the pointcloud that was used as input. The boundary 
mesh will encapsulate the entire model in visually a solid box. The clipping planes 
under the appearance tab in the GUI can be used to cut the boundary_mesh open to see 
inside. The shading mode for the boundary mesh can also be set to wireframe to make the 
'box' see-through. 

.. code:: python

    from pathlib import Path
    import dtcc

    # Build a mesh from raw data
    data_directory = Path("../data/helsingborg-residential-2022")
    p = dtcc.builder.parameters.default()
    p["data_directory"] = data_directory
    dtcc.builder.build(p)

    buildings_path = data_directory / "footprints.shp"
    pointcloud_path = data_directory

    origin, bounds = dtcc.builder.calculate_bounds(buildings_path, pointcloud_path, p)
    city = dtcc.io.load_city(buildings_path, bounds=bounds)
    pointcloud = dtcc.io.load_pointcloud(pointcloud_path, bounds=bounds)

    # Build a city
    city = dtcc.builder.build_city(city, pointcloud, bounds, p)

    # From the city build meshes
    volume_mesh, boundary_mesh = dtcc.builder.build_volume_mesh(city)

    # From the city build meshes
    ground_mesh, building_mesh = dtcc.builder.build_mesh(city, p)

    # Remove unwanted outliers from the point cloud
    pc = pointcloud.remove_global_outliers(3)

    # Create a scene and window. Add geometry to scene
    scene = dtcc.viewer.Scene()
    window = dtcc.viewer.Window(1200, 800)

    # Add meshes with data or colors to the scene for rendering.
    # To provide data for coloring the keyword argument "mesh_data="" is used.
    # To provied colors directly the keyword argument "mesh_colors=" is used. 
    scene.add_mesh("Building mesh", building_mesh)
    scene.add_mesh("Ground mesh", ground_mesh)
    scene.add_mesh("Boundary mesh", boundary_mesh)

    # Add a pointcloud with data or colors to the scene for rendering.
    # To provide data for coloring the keyword argument "pc_data="" is used.
    # To provied colors directly the keyword argument "pc_colors=" is used. 
    scene.add_pointcloud("Point cloud", pc)

    # Render geometry
    window.render(scene)


Viewer controls
---------------

Once the DTCC Viewer is running and a graphics window has appeard, the viewport can be
navigated with the mouse according to::

- `Left mouse button` - Rotate the view around the camera target
- `Right mouse button` - Panning the view, thus moving the camera target
- `Scroll` - Zoom in and out at the current camera target

A GUI is also created with global controls for the whole scene under
apperance which includes things like (background color and clipping planes etc). 
Individual GUI components are also created for each Mesh and Point Cloud that is 
added to the scene. To close the viewer click the regular closing symbol in the 
upper left corner of the window or press the ESC key. 

