import numpy as np
from dtcc import VolumeMesh
from collections import defaultdict
from timeit import default_timer as timer

"""
Notes: 
---
- LLoyd smoothing without any changes to ground height or other boundary surfaces

To Do:
- Add new position steps to set ground vertices to their final position
- Add new position projection to move wall boundary vertices on boudary plane.
- Move to buildings (Interior,Boundary)
"""


def find_boundary_nodes_via_connectivity(volume_mesh: VolumeMesh):
    """
    Identify boundary nodes in a tetrahedral mesh.

    Parameters
    ----------
    volume_mesh : VolumeMesh
        A tetrahedral mesh containing cells and vertices.

    Returns
    -------
    np.ndarray
        Array of boundary node indices.
    """
    print("Searching for boundary markers...")
    face_counts = defaultdict(int)

    # For convenience, define a small helper function
    def sorted_face(a, b, c):
        return tuple(sorted([a, b, c]))

    # Count how often each face appears (a face is a combination of 3 node indices)
    for tet in volume_mesh.cells:
        i, j, k, l = tet
        faces = [
            sorted_face(i, j, k),
            sorted_face(i, j, l),
            sorted_face(i, k, l),
            sorted_face(j, k, l),
        ]
        for f in faces:
            face_counts[f] += 1

    # A face is a boundary face if face_counts == 1
    boundary_faces = [f for f, cnt in face_counts.items() if cnt == 1]

    # The boundary nodes are all nodes that appear in any boundary face
    boundary_nodes = set()
    for f in boundary_faces:
        for node_idx in f:
            boundary_nodes.add(node_idx)

    return np.array(list(boundary_nodes), dtype=int)


def compute_smoothing_markers(mesh: VolumeMesh):
    """
    Compute and update markers for the mesh vertices.

    Parameters
    ----------
    mesh : VolumeMesh
        The input volume mesh.

    Returns
    -------
    VolumeMesh
        The updated mesh with recalculated markers.
    """
    print("Recalculating Volume Mesh markers for lloyd smoothing")
    # Initialize markers to -1
    markers = mesh.markers

    # Find boundary nodes
    boundary_nodes = find_boundary_nodes_via_connectivity(mesh)
    print("Found", len(boundary_nodes), "boundary nodes")
    # Mark boundary nodes
    markers[mesh.markers == -4] = -5

    for node in boundary_nodes:
        if markers[node] < -3:
            markers[node] = -4

    mesh.markers = markers

    return mesh


def vertex__cell_adjacency(volume_mesh: VolumeMesh):
    """
    Compute vertex-to-cell adjacency for a mesh.

    Parameters
    ----------
    volume_mesh : VolumeMesh
        A tetrahedral mesh.

    Returns
    -------
    list of list of int
        A list where each index contains the list of cell indices adjacent to a vertex.
    """
    vertex_neighbours = defaultdict(list)

    for c, cell in enumerate(volume_mesh.cells.astype(int)):
        vertex_neighbours[cell[0]].append(c)
        vertex_neighbours[cell[1]].append(c)
        vertex_neighbours[cell[2]].append(c)
        vertex_neighbours[cell[3]].append(c)
    return vertex_neighbours


def tetrahedron_volume(
    v0: np.ndarray, v1: np.ndarray, v2: np.ndarray, v3: np.ndarray
) -> float:
    """
    Compute the volume of a tetrahedral cell.

    Parameters
    ----------
    v0, v1, v2, v3 : np.ndarray
        Coordinates of the four vertices of the cell.

    Returns
    -------
    float
        The volume of the tetrahedral cell.
    """
    return abs(np.linalg.det([v1 - v0, v2 - v0, v3 - v0])) / 6


def calculate_volumes(mesh: VolumeMesh) -> np.array:
    """
    Compute the volumes of all tetrahedral cells in the mesh.

    Parameters
    ----------
    mesh : VolumeMesh
        A tetrahedral mesh.

    Returns
    -------
    np.ndarray
        Array of cell volumes.
    """
    volume = np.zeros((mesh.num_cells))
    volume.fill(np.nan)

    volume = np.zeros((mesh.num_cells))
    volume.fill(np.nan)

    for c, cell in enumerate(mesh.cells.astype(int)):
        v0 = mesh.vertices[cell[0]]
        v1 = mesh.vertices[cell[1]]
        v2 = mesh.vertices[cell[2]]
        v3 = mesh.vertices[cell[3]]

        volume[c] = tetrahedron_volume(v0, v1, v2, v3)

    return volume


def tetrahedron_centroid(
    v0: np.ndarray, v1: np.ndarray, v2: np.ndarray, v3: np.ndarray
) -> np.ndarray:
    """
    Compute the centroid of a tetrahedral cell.

    Parameters
    ----------
    v0, v1, v2, v3 : np.ndarray
        Coordinates of the four vertices of the cell.

    Returns
    -------
    np.ndarray
        Coordinates of the centroid.
    """
    return (v0 + v1 + v2 + v3) / 4


def calculate_centroids(mesh: VolumeMesh) -> np.array:
    """
    Compute the centroids of all tetrahedral cells in the mesh.

    Parameters
    ----------
    mesh : VolumeMesh
        A tetrahedral mesh.

    Returns
    -------
    np.ndarray
        Array of cell centroids.
    """
    centroid = np.zeros((mesh.num_cells, 3))
    centroid.fill(np.nan)

    for c, cell in enumerate(mesh.cells.astype(int)):
        v0 = mesh.vertices[cell[0]]
        v1 = mesh.vertices[cell[1]]
        v2 = mesh.vertices[cell[2]]
        v3 = mesh.vertices[cell[3]]

        centroid[c] = tetrahedron_centroid(v0, v1, v2, v3)

    return centroid


def tetrahedron_circumcenter(v0, v1, v2, v3):
    # Solve equidistant equations for circumcenter
    A = np.array([2 * (v1 - v0), 2 * (v2 - v0), 2 * (v3 - v0)])
    B = np.array(
        [
            np.dot(v1, v1) - np.dot(v0, v0),
            np.dot(v2, v2) - np.dot(v0, v0),
            np.dot(v3, v3) - np.dot(v0, v0),
        ]
    )

    if np.linalg.cond(A) > 1e12:
        return np.mean([v0, v1, v2, v3], axis=0)  # Fallback to centroid
    else:
        return np.linalg.solve(A, B)


def calculate_circumcenters(mesh: VolumeMesh) -> np.ndarray:
    circumcenters = np.zeros((mesh.num_cells, 3))
    for c, cell in enumerate(mesh.cells.astype(int)):
        v0, v1, v2, v3 = mesh.vertices[cell]
        circumcenters[c] = tetrahedron_circumcenter(v0, v1, v2, v3)

    return circumcenters


def lloyd_smoothing(mesh: VolumeMesh, iterations: int = 100, alpha: float = 0.2):
    """
    Perform Lloyd smoothing on a tetrahedral mesh.

    Parameters
    ----------
    mesh : VolumeMesh
        A tetrahedral mesh.
    iterations : int, optional
        Number of smoothing iterations (default is 100).
    alpha : float, optional
        Smoothing parameter controlling the influence of new vertices (default is 0.2).

    Returns
    -------
    VolumeMesh
        The smoothed mesh.
    """
    print("Lloyd Smoothing")
    # Compute adjacency of each vertex (Vertex star)
    adjacency = vertex__cell_adjacency(mesh)
    # Compute smoothing markers
    # -1: building Halos
    # -2: ground
    # -3: Top of the domain
    # -4: Vertical walls of the domain
    # -5: Free nodes
    mesh = compute_smoothing_markers(mesh)

    # change for testing
    boundary_markers = (-1, -2, -3, -4)
    for iter in range(iterations):
        print("Lloyd Iteration", iter)
        start = timer()

        # Compute cell volumes and centroids
        cell_volumes = calculate_volumes(mesh)
        # cell_centroids = calculate_circumcenters(mesh)
        cell_centroids = calculate_centroids(mesh)
        new_vertices = np.zeros_like(mesh.vertices)
        # For each vertex, compute area-weighted average of centroids of adjacent faces
        for v_idx, marker in enumerate(mesh.markers):

            if marker in boundary_markers:
                new_vertices[v_idx] = mesh.vertices[v_idx]
                continue

            adj_cell_indices = adjacency[v_idx]
            # Sum of area * centroid for all adjacent faces
            total_weight = np.sum(cell_volumes[adj_cell_indices])
            prod = (
                cell_centroids[adj_cell_indices]
                * cell_volumes[adj_cell_indices, np.newaxis]
            )
            weighted_sum = np.sum(prod, axis=0)

            old_vertex = mesh.vertices[v_idx]
            new_vertex = weighted_sum / (total_weight + 1e-16)
            new_vertices[v_idx] = (1 - alpha) * old_vertex + alpha * new_vertex

        mesh.vertices = new_vertices
        print(f"Iteration {iter} completed in {timer() - start:.4f} seconds")
    return mesh


def create_cube_with_perturbed_center():
    """Create a cube mesh with a perturbed interior node."""
    # Cube vertices (8 corners + 1 perturbed center)
    vertices = np.array(
        [
            [0.0, 0.0, 0.0],  # 0
            [1.0, 0.0, 0.0],  # 1
            [1.0, 1.0, 0.0],  # 2
            [0.0, 1.0, 0.0],  # 3
            [0.0, 0.0, 1.0],  # 4
            [1.0, 0.0, 1.0],  # 5
            [1.0, 1.0, 1.0],  # 6
            [0.0, 1.0, 1.0],  # 7
            [0.6, 0.6, 0.6],  # 8 (perturbed center)
        ]
    )

    # Tetrahedrons connecting faces to the center (12 cells)
    cells = np.array(
        [
            [0, 1, 2, 8],  # Bottom face (z=0)
            [0, 2, 3, 8],
            [4, 5, 6, 8],  # Top face (z=1)
            [4, 6, 7, 8],
            [0, 1, 5, 8],  # Front face (y=0)
            [0, 5, 4, 8],
            [2, 3, 7, 8],  # Back face (y=1)
            [2, 7, 6, 8],
            [0, 3, 7, 8],  # Left face (x=0)
            [0, 7, 4, 8],
            [1, 2, 6, 8],  # Right face (x=1)
            [1, 6, 5, 8],
        ]
    )

    # Markers: -4 for boundary nodes (corners), -5 for free node (center)
    markers = np.full(len(vertices), -4, dtype=int)
    markers[[0, 1, 2, 3, 8]] = -5  # Free interior node

    return VolumeMesh(vertices=vertices, cells=cells, markers=markers)


if __name__ == "__main__":

    mesh = create_cube_with_perturbed_center()
    mesh.save("cube.vtu")
    # Perform Lloyd smoothing
    mesh = lloyd_smoothing(mesh, iterations=10, alpha=0.2)

    # Save the smoothed mesh
    mesh.save("smoothed_cube2.vtu")
