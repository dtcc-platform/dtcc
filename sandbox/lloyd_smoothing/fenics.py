def write_mesh_to_xml(mesh, filename):
    """
    Write a tetrahedral mesh to a FEniCS XML file.

    The mesh object is assumed to have:
      - mesh.vertices: a NumPy array of shape (num_vertices, dim)
      - mesh.cells:    a NumPy array of shape (num_cells, 4)

    Parameters:
      mesh:   Mesh object with .vertices and .cells attributes.
      filename: Output filename (e.g., "mesh.xml").
    """
    import numpy as np

    vertices = mesh.vertices
    cells = mesh.cells
    num_vertices = vertices.shape[0]
    num_cells = cells.shape[0]
    dim = vertices.shape[1]

    # Determine cell type based on number of vertices per cell.
    # For tetrahedral meshes, we expect 4 vertices per cell.
    if cells.shape[1] == 4:
        cell_tag = "tetrahedron"
    elif cells.shape[1] == 3:
        cell_tag = "triangle"
    else:
        raise ValueError(
            "Unsupported cell type: expected 3 (triangle) or 4 (tetrahedron) vertices per cell."
        )

    with open(filename, "w") as f:
        # Write the XML header and dolfin tag.
        f.write('<?xml version="1.0"?>\n')
        f.write('<dolfin xmlns:dolfin="http://fenicsproject.org">\n')

        # Start the mesh element with cell type and dimension.
        f.write('  <mesh celltype="{}" dim="{}">\n'.format(cell_tag, dim))

        # Write the vertices.
        f.write('    <vertices size="{}">\n'.format(num_vertices))
        for i, v in enumerate(vertices):
            if dim == 2:
                f.write(
                    '      <vertex index="{}" x="{:.15e}" y="{:.15e}" />\n'.format(
                        i, v[0], v[1]
                    )
                )
            elif dim == 3:
                f.write(
                    '      <vertex index="{}" x="{:.15e}" y="{:.15e}" z="{:.15e}" />\n'.format(
                        i, v[0], v[1], v[2]
                    )
                )
        f.write("    </vertices>\n")

        # Write the cells.
        f.write('    <cells size="{}">\n'.format(num_cells))
        for i, cell in enumerate(cells):
            if cell_tag == "tetrahedron":
                f.write(
                    '      <tetrahedron index="{}" v0="{}" v1="{}" v2="{}" v3="{}" />\n'.format(
                        i, cell[0], cell[1], cell[2], cell[3]
                    )
                )
            elif cell_tag == "triangle":
                f.write(
                    '      <triangle index="{}" v0="{}" v1="{}" v2="{}" />\n'.format(
                        i, cell[0], cell[1], cell[2]
                    )
                )
        f.write("    </cells>\n")

        # Close the mesh and dolfin elements.
        f.write("  </mesh>\n")
        f.write("</dolfin>\n")
