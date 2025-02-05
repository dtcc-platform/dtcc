import numpy as np
from dtcc import VolumeMesh  # using your existing mesh class
from collections import defaultdict


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


def tetrahedron_volume(v0, v1, v2, v3):
    """Compute the absolute volume of a tetrahedron."""
    return abs(np.linalg.det(np.array([v1 - v0, v2 - v0, v3 - v0]))) / 6.0


def tetrahedron_centroid(v0, v1, v2, v3):
    """Compute the centroid of a tetrahedron."""
    return (v0 + v1 + v2 + v3) / 4.0


def compute_tet_quality(v0, v1, v2, v3):
    """
    Compute an edge-based quality metric for a tetrahedron.
    For a regular tetrahedron the value is 1, and it decreases toward 0 as the cell becomes degenerate.
    """
    vol = tetrahedron_volume(v0, v1, v2, v3)
    if vol <= 0:
        return 0.0
    # Compute all 6 edge lengths.
    edges = [
        np.linalg.norm(v1 - v0),
        np.linalg.norm(v2 - v0),
        np.linalg.norm(v3 - v0),
        np.linalg.norm(v2 - v1),
        np.linalg.norm(v3 - v1),
        np.linalg.norm(v3 - v2),
    ]
    sum_sq = sum(e**2 for e in edges)
    quality = 12 * (3 * vol) ** (2 / 3) / sum_sq
    return quality


def compute_adjacency(mesh):
    """
    Build a dictionary mapping each vertex index to a list of unique cell indices that include that vertex.
    """
    adjacency = defaultdict(set)
    for c, cell in enumerate(mesh.cells.astype(int)):
        for v in cell:
            adjacency[v].add(c)
    # Convert each set to a list.
    for v in adjacency:
        adjacency[v] = list(adjacency[v])
    return adjacency


def compute_current_min_quality(v_idx, mesh, adjacency):
    """
    Compute the minimum quality among all tetrahedra adjacent to vertex v_idx,
    using the current vertex positions.
    """
    current_min = float("inf")
    for cell_idx in adjacency[v_idx]:
        cell = mesh.cells[cell_idx].astype(int)
        tet_verts = np.array([mesh.vertices[vid] for vid in cell])
        q = compute_tet_quality(tet_verts[0], tet_verts[1], tet_verts[2], tet_verts[3])
        if q < current_min:
            current_min = q
    return current_min


def quality_improvement_check(v_idx, candidate, mesh, adjacency, tol=1e-6):
    """
    Compute the minimum quality among all tetrahedra adjacent to vertex v_idx,
    if vertex v_idx were moved to 'candidate'. Compare it to the current minimum quality.

    Returns:
      improvement (bool): True if candidate minimum quality > current minimum quality + tol.
      current_min (float): current minimum quality.
      candidate_min (float): candidate's minimum quality.
    """
    current_min = float("inf")
    candidate_min = float("inf")
    for cell_idx in adjacency[v_idx]:
        cell = mesh.cells[cell_idx].astype(int)
        # Current configuration:
        current_tet = np.array([mesh.vertices[vid] for vid in cell])
        q_current = compute_tet_quality(
            current_tet[0], current_tet[1], current_tet[2], current_tet[3]
        )
        if q_current < current_min:
            current_min = q_current
        # Candidate configuration: substitute candidate for vertex v_idx.
        candidate_tet = np.array(
            [candidate if vid == v_idx else mesh.vertices[vid] for vid in cell]
        )
        q_candidate = compute_tet_quality(
            candidate_tet[0], candidate_tet[1], candidate_tet[2], candidate_tet[3]
        )
        if q_candidate < candidate_min:
            candidate_min = q_candidate
    improvement = candidate_min > (current_min + tol)
    return improvement, current_min, candidate_min


def lloyd_smoothing_adaptive(mesh, iterations=1, alpha=0.2, max_attempts=5, tol=1e-6):
    """
    Perform Lloyd smoothing on a tetrahedral mesh with quality control and local adaptive step sizing,
    using a relative improvement condition.

    For each interior vertex (marker not in boundary_markers), compute a volume-weighted centroid
    of adjacent tetrahedra. Then, try to update the vertex by blending:
         candidate = (1 - local_alpha)*old_position + local_alpha*centroid.

    Instead of a fixed quality threshold, we require that the candidate move improves the worst-case
    (minimum) quality among adjacent tetrahedra compared to the current configuration.

    If a candidate yields an improvement, it is accepted immediately. Otherwise, we reduce the step
    size (local_alpha) and try again (up to max_attempts). If no candidate yields an improvement,
    we update the vertex only if the best candidate found gives a slight improvement (beyond tol),
    otherwise we leave it unchanged.

    Parameters:
      mesh: a VolumeMesh instance.
      iterations: number of smoothing iterations.
      alpha: initial blending parameter.
      boundary_markers: vertices with these marker values are not updated.
      max_attempts: maximum number of candidate moves (with reducing alpha) to try.
      tol: tolerance for considering an improvement.

    Returns:
      The smoothed mesh.
    """
    adjacency = compute_adjacency(mesh)

    # Compute smoothing markers
    # -1: building Halos
    # -2: ground
    # -3: Top of the domain
    # -4: Vertical walls of the domain
    # -5: Free nodes
    mesh = compute_smoothing_markers(mesh)
    boundary_markers = (-1, -2, -3, -4)

    for it in range(iterations):
        # Compute volumes and centroids for all tetrahedral cells.
        cell_vols = np.array(
            [
                tetrahedron_volume(*mesh.vertices[cell])
                for cell in mesh.cells.astype(int)
            ]
        )
        cell_cents = np.array(
            [
                tetrahedron_centroid(*mesh.vertices[cell])
                for cell in mesh.cells.astype(int)
            ]
        )

        new_vertices = mesh.vertices.copy()
        for v_idx, marker in enumerate(mesh.markers):
            # Skip boundary vertices.
            if marker in boundary_markers:
                continue

            cells_adj = adjacency.get(v_idx, [])
            if not cells_adj:
                continue

            # Compute volume-weighted average of the centroids for cells adjacent to v_idx.
            weights = cell_vols[cells_adj]
            total_weight = np.sum(weights)
            if total_weight < 1e-16:
                continue

            weighted_sum = np.sum(
                cell_cents[cells_adj] * weights[:, np.newaxis], axis=0
            )
            centroid = weighted_sum / total_weight

            old_position = mesh.vertices[v_idx]
            # Compute current minimum quality for this vertex.
            current_min = compute_current_min_quality(v_idx, mesh, adjacency)

            local_alpha = alpha
            best_candidate = old_position
            best_candidate_quality = current_min
            accepted = False
            for attempt in range(max_attempts):
                candidate = (1 - local_alpha) * old_position + local_alpha * centroid
                improvement, cur_min, cand_min = quality_improvement_check(
                    v_idx, candidate, mesh, adjacency, tol=tol
                )
                if improvement:
                    best_candidate = candidate
                    best_candidate_quality = cand_min
                    accepted = True
                    # Debug: print(f"Vertex {v_idx} accepted candidate with quality improvement: {cur_min:.4f} -> {cand_min:.4f}")
                    break
                else:
                    # Save candidate if it's the best so far.
                    if cand_min > best_candidate_quality:
                        best_candidate = candidate
                        best_candidate_quality = cand_min
                    local_alpha /= 2.0

            # Update the vertex if the best candidate gives an improvement over the current quality.
            if best_candidate_quality > (current_min + tol):
                new_vertices[v_idx] = best_candidate
            else:
                # Optionally print a message if no improvement was possible.
                # print(
                #    f"Vertex {v_idx}: no candidate improved quality (current {current_min:.4f}, best candidate {best_candidate_quality:.4f}); retaining old position."
                # )
                new_vertices[v_idx] = old_position

        mesh.vertices = new_vertices
        print(f"Iteration {it} completed.")

    return mesh


def create_cube_with_perturbed_center():
    """
    Create a simple cube mesh with eight corner nodes and one interior node.
    The cube is subdivided into 12 tetrahedra.
    Boundary vertices (the 8 cube corners) are marked as -1 (fixed), and the interior node is marked as 0.
    """
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
            [0.6, 0.6, 0.6],  # 8 (interior)
        ]
    )

    cells = np.array(
        [
            [0, 1, 2, 8],
            [0, 2, 3, 8],
            [4, 5, 6, 8],
            [4, 6, 7, 8],
            [0, 1, 5, 8],
            [0, 5, 4, 8],
            [2, 3, 7, 8],
            [2, 7, 6, 8],
            [0, 3, 7, 8],
            [0, 7, 4, 8],
            [1, 2, 6, 8],
            [1, 6, 5, 8],
        ]
    )

    markers = np.full(len(vertices), 0, dtype=int)
    markers[0:8] = -1  # cube corners are fixed
    return VolumeMesh(vertices=vertices, cells=cells, markers=markers)


lloyd_smoothing = lloyd_smoothing_adaptive

if __name__ == "__main__":
    # Create the test mesh.
    mesh = create_cube_with_perturbed_center()

    # Print initial tetrahedron qualities.
    print("Initial tetrahedron qualities:")
    for i, cell in enumerate(mesh.cells.astype(int)):
        verts = mesh.vertices[cell]
        q = compute_tet_quality(verts[0], verts[1], verts[2], verts[3])
        print(f"Cell {i}: quality = {q:.4f}")

    # Perform 3 iterations of smoothing with adaptive step sizing based on quality improvement.
    mesh = lloyd_smoothing_adaptive(
        mesh, iterations=3, alpha=0.2, max_attempts=5, tol=1e-6
    )

    # Print updated vertex positions and tetrahedron qualities.
    print("\nVertex positions after adaptive smoothing:")
    print(mesh.vertices)

    print("\nTetrahedron qualities after adaptive smoothing:")
    for i, cell in enumerate(mesh.cells.astype(int)):
        verts = mesh.vertices[cell]
        q = compute_tet_quality(verts[0], verts[1], verts[2], verts[3])
        print(f"Cell {i}: quality = {q:.4f}")
