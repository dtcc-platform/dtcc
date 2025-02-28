# Testing Lloyd smoothing

import numpy as np
import dtcc
from plotting import plot_mesh, show


def compute_face_centroids_and_areas(mesh):
    """
    Given a 2D triangular mesh, compute centroids and (signed) areas for each face.
    Returns:
      face_centroids: (F, 2)
      face_areas:     (F,)   (these will be positive magnitudes for areas)
    """
    # Gather the vertex positions for each face
    v0 = mesh.vertices[mesh.faces[:, 0]]
    v1 = mesh.vertices[mesh.faces[:, 1]]
    v2 = mesh.vertices[mesh.faces[:, 2]]

    # Face centroids = average of the 3 vertices
    face_centroids = (v0 + v1 + v2) / 3.0

    # Areas via cross product method (for 2D, treat as vectors in R^2)
    # area_triangle = 0.5 * |(v1 - v0) x (v2 - v0)|
    # In 2D, cross([x1, y1], [x2, y2]) = x1*y2 - x2*y1 (scalar).
    cross_vals = (v1[:, 0] - v0[:, 0]) * (v2[:, 1] - v0[:, 1]) - (
        v1[:, 1] - v0[:, 1]
    ) * (v2[:, 0] - v0[:, 0])
    face_areas = 0.5 * np.abs(cross_vals)

    return face_centroids, face_areas


def build_vertex_face_adjacency(mesh):
    """
    Build a list of faces adjacent to each vertex.
    Returns:
      adjacency: a list of length V, where adjacency[v] is a list
                 of face indices incident on vertex v.
    """
    num_vertices = mesh.vertices.shape[0]
    adjacency = [[] for _ in range(num_vertices)]

    for f_idx, face in enumerate(mesh.faces):
        for v in face:
            adjacency[v].append(f_idx)

    return adjacency


def find_boundary_vertices(mesh):
    # Compute boundary vertices

    edges_count = {}

    # For each face, extract its 3 edges in a canonical (sorted) form
    for face in mesh.faces:
        for i in range(3):
            v1 = face[i]
            v2 = face[(i + 1) % 3]
            # Sort the indices so edge is always stored as (min, max)
            e = (min(v1, v2), max(v1, v2))
            edges_count[e] = edges_count.get(e, 0) + 1

    # Collect vertices that appear in edges that only have a count of 1
    boundary_verts = set()
    for (v1, v2), count in edges_count.items():
        if count == 1:
            boundary_verts.add(v1)
            boundary_verts.add(v2)

    return set(np.array(sorted(boundary_verts), dtype=int))


def lloyd_smoothing(mesh, boundary, num_iterations=3, alpha=0.2):
    "LLoyd smoothing"

    # Compute adjacency
    adjacency = build_vertex_face_adjacency(mesh)

    # Iteratively update vertex positions
    for iter in range(num_iterations):

        print("Iteration", iter)

        # Compute face centroids and areas
        face_centroids, face_areas = compute_face_centroids_and_areas(mesh)

        # Prepare an array for new vertex positions
        new_vertices = np.zeros_like(mesh.vertices)

        # For each vertex, compute area-weighted average of centroids of adjacent faces
        for v_idx in range(mesh.vertices.shape[0]):

            # Skip boundary vertices
            if v_idx in boundary:
                new_vertices[v_idx] = mesh.vertices[v_idx]
                continue

            # Sum of area * centroid for all adjacent faces
            f_indices = adjacency[v_idx]
            total_weight = np.sum(face_areas[f_indices])
            weighted_sum = np.sum(
                face_centroids[f_indices] * face_areas[f_indices, np.newaxis], axis=0
            )

            # New position is the area-weighted centroid
            old_vertex = mesh.vertices[v_idx]
            new_vertex = weighted_sum / (total_weight + 1e-16)
            new_vertices[v_idx] = (1 - alpha) * old_vertex + alpha * new_vertex

            new_vertices[v_idx] = weighted_sum / (total_weight + 1e-16)

        # Update the mesh vertices
        mesh.vertices = new_vertices


def test_simple_mesh():

    # Create a simple mesh of the unit square
    vertices = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
    )
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    mesh = dtcc.Mesh(vertices=vertices, faces=faces)

    # Find boundary vertices
    boundary = find_boundary_vertices(mesh)
    print(boundary)

    # Lloyd smoothing
    lloyd_smoothing(mesh, boundary)


def test_ground_mesh():

    # Load ground mesh
    mesh = dtcc.load_mesh("ground_mesh.")
    plot_mesh(mesh, show=False)
    # mesh.view()

    # Find boundary vertices
    boundary = find_boundary_vertices(mesh)
    print(boundary)

    # Lloyd smoothing
    lloyd_smoothing(mesh, boundary, num_iterations=10)
    plot_mesh(mesh, show=True)

    show()


if __name__ == "__main__":

    # test_simple_mesh()
    test_ground_mesh()
