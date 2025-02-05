from fenics import *
import math
import numpy as np

from mesh_quality import aspect_ratio_stats

H = 15.0
dem = "H*sin(5*pi*(x[0]-xmin)/A)*sin(5*pi*(x[1]-ymin)/B)"


def bounds(mesh):
    xmin = np.min(mesh.coordinates()[:, 0])
    xmax = np.max(mesh.coordinates()[:, 0])
    ymin = np.min(mesh.coordinates()[:, 1])
    ymax = np.max(mesh.coordinates()[:, 1])
    zmin = np.min(mesh.coordinates()[:, 2])
    zmax = np.max(mesh.coordinates()[:, 2])
    return xmin, xmax, ymin, ymax, zmin, zmax


def print_mesh_quality(mesh, u):

    # V = VectorFunctionSpace(mesh, "CG", 1)
    # displacement = Expression(("0", "0", "x[0]"), degree=1)
    # u = project(displacement, V)

    # Get displacement of the mesh vertices
    n = mesh.coordinates().shape[0]
    d = 3
    dx = u.compute_vertex_values(mesh).reshape((d, n)).T

    class _Mesh:
        pass

    _mesh = _Mesh()
    _mesh.vertices = mesh.coordinates() + dx
    _mesh.cells = mesh.cells()

    min_ar, max_ar, median_ar = aspect_ratio_stats(_mesh)
    print(f"Mesh quality: min={min_ar:.3g}, max={max_ar:.3g}, median={median_ar:.3g}")

    # Save as VTK for visualization
    __mesh = Mesh()
    editor = MeshEditor()
    editor.open(__mesh, "tetrahedron", 3, 3)
    editor.init_vertices(_mesh.vertices.shape[0])
    editor.init_cells(_mesh.cells.shape[0])
    for i, v in enumerate(_mesh.vertices):
        editor.add_vertex(i, v)
    for i, c in enumerate(_mesh.cells):
        editor.add_cell(i, c)
    editor.close()
    File("deformed.pvd") << __mesh


# ---------------------------------------------------------------------------
# Laplacian smoothing: solve for the scalar z-displacement,
# then project to a 3D displacement field.
def laplacian_smoothing_disp(mesh):

    # Get mesh bounds
    xmin, xmax, ymin, ymax, zmin, zmax = bounds(mesh)
    A = xmax - xmin
    B = ymax - ymin

    # Solve a scalar Laplace problem for the z-displacement.
    V = FunctionSpace(mesh, "CG", 1)
    u = TrialFunction(V)
    v = TestFunction(V)
    a = inner(grad(u), grad(v)) * dx
    L = Constant(0.0) * v * dx

    tol = 1e-14

    def lower_boundary(x, on_boundary):
        return on_boundary and near(x[2], zmin, tol)

    # Prescribe u = 0.25*sin(2*pi*x[0])*sin(2*pi*x[1]) on the lower face.
    bc_expr = Expression(
        dem,
        degree=2,
        pi=math.pi,
        H=H,
        A=A,
        B=B,
        xmin=xmin,
        ymin=ymin,
    )
    bc = DirichletBC(V, bc_expr, lower_boundary)

    u_sol = Function(V)
    solve(a == L, u_sol, bc)

    # Project the scalar solution to a vector field (0,0,u_sol).
    V_vec = VectorFunctionSpace(mesh, "CG", 1)
    u_disp = project(as_vector([0.0, 0.0, u_sol]), V_vec)

    return u_disp


# ---------------------------------------------------------------------------
# Elasticity smoothing: solve directly for the displacement vector.
def elasticity_smoothing_disp(mesh):

    # Get mesh bounds
    xmin, xmax, ymin, ymax, zmin, zmax = bounds(mesh)
    A = xmax - xmin
    B = ymax - ymin

    V = VectorFunctionSpace(mesh, "CG", 1)
    u = TrialFunction(V)
    v = TestFunction(V)

    # Material parameters
    E = 1.0  # Young's modulus
    nu = 0.45  # Poisson ratio
    lambda_ = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))

    # Over-stiffen the volumetric part
    # lambda_ *= 2.0

    # Define strain and stress
    def epsilon(u):
        return sym(grad(u))

    def sigma(u):
        return lambda_ * div(u) * Identity(3) + 2 * mu * epsilon(u)

    a = inner(sigma(u), epsilon(v)) * dx
    L = dot(Constant((0.0, 0.0, 0.0)), v) * dx

    # Does not seem to help
    # alpha = 10.0  # Choose an appropriate penalty parameter.
    # a = a + alpha * inner(div(u), div(v)) * dx

    tol = 1e-14

    def lower_boundary(x, on_boundary):
        return on_boundary and near(x[2], zmin, tol)

    # (a) Lower face: prescribe full displacement.
    bc_expr = Expression(
        ("0", "0", dem),
        degree=2,
        pi=math.pi,
        H=H,
        A=A,
        B=B,
        xmin=xmin,
        ymin=ymin,
    )
    bc_lower = DirichletBC(V, bc_expr, lower_boundary)

    # (b) Other boundaries: fix the x- and y-components to zero.
    def other_boundary(x, on_boundary):
        return on_boundary and (not near(x[2], zmin, tol))

    bc_x = DirichletBC(V.sub(0), Constant(0.0), other_boundary)
    bc_y = DirichletBC(V.sub(1), Constant(0.0), other_boundary)
    bcs = [bc_lower, bc_x, bc_y]

    u_sol = Function(V)
    solve(a == L, u_sol, bcs)

    return u_sol


# ---------------------------------------------------------------------------
# Main script: create the original mesh, solve both problems,
# and save the displacement fields.
def main():
    # Create a unit cube mesh
    # mesh = UnitCubeMesh(1, 1, 1)

    # Load mesh from file
    mesh = Mesh("mesh.xml")

    # Save original mesh to file
    File("original.pvd") << mesh

    # Laplacian smoothing displacement (projected to a vector field)
    u_laplace_disp = laplacian_smoothing_disp(mesh)
    File("laplacian.pvd") << u_laplace_disp

    # Elasticity smoothing displacement (vector solution)
    u_elastic_disp = elasticity_smoothing_disp(mesh)
    File("elastic.pvd") << u_elastic_disp

    # Print mesh quality statistics
    print_mesh_quality(mesh, u_laplace_disp)
    print_mesh_quality(mesh, u_elastic_disp)


if __name__ == "__main__":
    main()
