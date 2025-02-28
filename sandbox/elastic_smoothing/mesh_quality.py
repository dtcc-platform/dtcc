import numpy as np


def tetrahedron_volume(v0, v1, v2, v3):
    """
    Compute the volume of a tetrahedron given its four vertices.
    """
    return abs(np.dot(v1 - v0, np.cross(v2 - v0, v3 - v0))) / 6.0


def face_area(v0, v1, v2):
    """
    Compute the area of a triangle (face) given its three vertices.
    """
    return 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0))


def tetrahedron_circumcenter(v0, v1, v2, v3):
    """
    Compute the circumcenter of a tetrahedron.

    Uses the formula:
      c = v0 + ( ||A||² × (B×C) + ||B||² × (C×A) + ||C||² × (A×B) )
          / (2 * (A · (B×C)) )
    where A = v1-v0, B = v2-v0, C = v3-v0.
    """
    A = v1 - v0
    B = v2 - v0
    C = v3 - v0
    # Compute weighted cross products.
    alpha = np.linalg.norm(A) ** 2 * np.cross(B, C)
    beta = np.linalg.norm(B) ** 2 * np.cross(C, A)
    gamma = np.linalg.norm(C) ** 2 * np.cross(A, B)
    denominator = 2.0 * np.dot(A, np.cross(B, C))
    if denominator == 0:
        # Degenerate tetrahedron: return v0 as fallback.
        return v0
    return v0 + (alpha + beta + gamma) / denominator


def tet_aspect_ratio(v0, v1, v2, v3):
    """
    Compute the normalized aspect ratio of a tetrahedron.

    The algorithm is as follows:
      1. Compute the volume V.
      2. Compute the areas of the four faces (A0, A1, A2, A3) and set A = sum(A_i).
      3. Compute the inradius: r = 3V / A.
      4. Compute the circumcenter c and circumradius: R = ||c - v0||.
      5. The normalized aspect ratio is then defined as (R/r)/3.

    (For a regular tetrahedron, this ratio equals 1.)
    """
    V = tetrahedron_volume(v0, v1, v2, v3)
    if V == 0:
        return 0.0  # Degenerate tetrahedron.

    A0 = face_area(v1, v2, v3)
    A1 = face_area(v0, v2, v3)
    A2 = face_area(v0, v1, v3)
    A3 = face_area(v0, v1, v2)
    A = A0 + A1 + A2 + A3

    # Inradius
    r = 3.0 * V / A

    # Circumcenter and circumradius.
    c = tetrahedron_circumcenter(v0, v1, v2, v3)
    R = np.linalg.norm(c - v0)

    # Normalized aspect ratio (dividing by 3 makes the value 1 for a regular tetrahedron).
    ar = (R / r) / 3.0
    return ar


def mesh_aspect_ratios(mesh):
    """
    Compute the normalized aspect ratio for each tetrahedron in the mesh.

    Returns a NumPy array of aspect ratios.
    """
    aspect_ratios = []
    for cell in mesh.cells:
        v0 = mesh.vertices[cell[0]]
        v1 = mesh.vertices[cell[1]]
        v2 = mesh.vertices[cell[2]]
        v3 = mesh.vertices[cell[3]]
        ar = tet_aspect_ratio(v0, v1, v2, v3)
        aspect_ratios.append(ar)
    return np.array(aspect_ratios)


def aspect_ratio_stats(mesh):
    """
    Compute basic statistics (min, max, median) of the normalized aspect ratio
    over all tetrahedra in the mesh.

    Returns a tuple (min_ar, max_ar, median_ar).
    """
    ars = mesh_aspect_ratios(mesh)
    min_ar = np.min(ars)
    max_ar = np.max(ars)
    median_ar = np.median(ars)
    return min_ar, max_ar, median_ar


# Example usage:
if __name__ == "__main__":
    # Suppose we have a mesh object with .vertices and .cells.
    # For demonstration, here is a dummy mesh with two tetrahedra.
    class DummyMesh:
        pass

    mesh = DummyMesh()
    # Example: four vertices for a single tetrahedron.
    mesh.vertices = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    )
    # One tetrahedron using these four vertices.
    mesh.cells = np.array([[0, 1, 2, 3]])

    ars = mesh_aspect_ratios(mesh)
    print("Aspect ratios for each tetrahedron:", ars)
    print("Mesh quality (min, max, median):", aspect_ratio_stats(mesh))
