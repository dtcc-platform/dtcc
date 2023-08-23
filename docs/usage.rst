Usage
=====



Visualisation
------------

The DTCC platform provides an integrated viewer which has the capability 
to display large quatities of geometry, including meshes and point clouds.

To visualise a point cloud colored by the x-position of the points:

.. code:: python

    from dtcc_io import pointcloud
    filename_pc = '../../../data/models/pointcloud.las'
    pc = pointcloud.load(filename_pc)
    color_data = pc.points[:,0]
    pc.view(pc_data = color_data)

To visualise a mesh without data (default coloring schema will be vertex
z-value):

.. code:: python

    from dtcc_io import meshes
    filename_mesh = '../../../data/models/mesh.obj'
    mesh = meshes.load_mesh(filename_mesh)
    mesh.view()

To visualise a point cloud and a mesh in the same window:

.. code:: python

    from dtcc_io import meshes
    from dtcc_io import pointcloud
    filename_mesh = '../../../data/models/mesh.obj'
    filename_pc = '../../../data/models/pointcloud.csv'
    pc = pointcloud.load(filename_pc)
    mesh = meshes.load_mesh(filename_mesh)
    pc.view(mesh=mesh)

The same principle works the other way around, where the pointclode is
added as an argument to the mesh viewing function call:

.. code:: python

    from dtcc_io import meshes
    from dtcc_io import pointcloud
    filename_mesh = '../../../data/models/mesh.obj'
    filename_pc = '../../../data/models/pointcloud.csv'
    pc = pointcloud.load(filename_pc)
    mesh = meshes.load_mesh(filename_mesh)
    mesh.view(pc=pc)


DTCC Viewer can also be used to visualise multiple meshes and point clouds
using a slightly different approch:

.. code:: python

    from dtcc_io import meshes
    from dtcc_io import pointcloud

    window = Window(1200, 800)

    # Import meshes to be viewed
    mesh_a = meshes.load_mesh("../../../data/models/CitySurfaceA.obj")
    mesh_b = meshes.load_mesh("../../../data/models/CitySurfaceB.obj")

    # Create data for coloring each mesh
    mesh_data_a = mesh_a.vertices[:, 1]
    mesh_data_b = mesh_b.vertices[:, 0]
    meshes_imported = [mesh_a, mesh_b]

    # Import point clodus to be viewed
    pc_a = pointcloud.load("../../../data/models/PointCloud_HQ_A.csv")
    pc_b = pointcloud.load("../../../data/models/PointCloud_HQ_B.csv")
    
    # Create data for coloring each mesh
    pc_data_a = pc_a.points[:, 0]
    pc_data_b = pc_b.points[:, 1]
    pcs_imported = [pc_a, pc_b]

    # Calculate common recentering vector base of the bounding box of all combined vertices.
    recenter_vec = calc_multi_geom_recenter_vector(meshes_imported, pcs_imported)

    # Create MeshData object where all the data for each mesh is formated for OpengGL calls
    mesh_data_obj_a = MeshData("mesh A", mesh_a, mesh_data_a, recenter_vec)
    mesh_data_obj_b = MeshData("mesh B", mesh_b, mesh_data_b, recenter_vec)
    mesh_data_list = [mesh_data_obj_a, mesh_data_obj_b]

    # Create PointCloudData object where all the data for each pc is formated for OpengGL calls
    pc_data_obj_a = PointCloudData("point cloud A", pc_a, pc_data_a, recenter_vec)
    pc_data_obj_b = PointCloudData("point cloud B", pc_b, pc_data_b, recenter_vec)
    pc_data_list = [pc_data_obj_a, pc_data_obj_b]


    window.render_multi(mesh_data_list, pc_data_list)


