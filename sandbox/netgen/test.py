#!/usr/bin/env python3
"""
Netgen → NumPy → VTU (2D polygons with optional nesting and interfaces)

Dependencies:
    pip install netgen-mesher meshio numpy
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict
import numpy as np
import meshio
from netgen.geom2d import SplineGeometry
from netgen.meshing import MeshingParameters
import re
import time
import sys

_t = None  # for timing


def tic():
    global _t
    _t = time.time()


def toc(task: Optional[str] = None):
    global _t
    if _t is None:
        raise RuntimeError("Must call tic() before toc()")
    dt = time.time() - _t
    _t = None
    if task:
        print(f"Elapsed time: {dt:.3f} s for {task}")
    else:
        print(f"Elapsed time: {dt:.3f} s")
    return dt


def make_mp_fast(maxh=1.0):
    mp = MeshingParameters(maxh=maxh)
    for k, v in {
        "optimize2d": "",  # disable smoothing / swaps
        "grading": 0.7,  # allow faster size growth
        "segmentsperedge": 0.5,  # fewer splits per edge
        "curvaturesafety": 1.0,  # fine for straight lines
        "check_overlap": 0,  # skip heavy checks (if you already validate)
        "check_overlapping_boundary": 0,
    }.items():
        if hasattr(mp, k):
            setattr(mp, k, v)
    return mp


# ------------- Types -------------
XY = Tuple[float, float]
Loop = List[XY]

# ------------- Geometry helpers -------------


def signed_area(poly: Loop) -> float:
    """Positive for CCW, negative for CW."""
    A = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        A += x1 * y2 - x2 * y1
    return 0.5 * A


def polygon_centroid(poly: Loop) -> XY:
    """Centroid for simple polygon; falls back to vertex average if degenerate."""
    A2 = 0.0
    Cx = 0.0
    Cy = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        c = x1 * y2 - x2 * y1
        A2 += c
        Cx += (x1 + x2) * c
        Cy += (y1 + y2) * c
    if abs(A2) < 1e-30:
        xs, ys = zip(*poly)
        n = len(poly)
        return (sum(xs) / n, sum(ys) / n)
    A = A2 / 2.0
    return (Cx / (6 * A), Cy / (6 * A))


def point_in_polygon(pt: XY, poly: Loop) -> bool:
    """Ray casting; True if inside (treats boundary as outside for robustness)."""
    x, y = pt
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-300) + x1
            if xin > x:
                inside = not inside
    return inside


def tri_centroid(points_xyz: np.ndarray, tri: np.ndarray) -> XY:
    a, b, c = points_xyz[tri[0]], points_xyz[tri[1]], points_xyz[tri[2]]
    return ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0)


# ------------- File I/O helpers -------------


def tokens_to_pairs(tokens: List[str]) -> Loop:
    if len(tokens) % 2 != 0:
        raise ValueError(
            f"Odd number of coordinates ({len(tokens)}); expected x y x y ..."
        )
    it = iter(tokens)
    return [(float(x), float(y)) for x, y in zip(it, it)]


def dedupe_closing_vertex(coords: Loop, tol: float = 1e-12) -> Loop:
    """Remove last point if it duplicates the first."""
    if len(coords) >= 2:
        x0, y0 = coords[0]
        x1, y1 = coords[-1]
        if abs(x0 - x1) <= tol and abs(y0 - y1) <= tol:
            return coords[:-1]
    return coords


def read_loops_from_file(path: str) -> Tuple[Loop, List[Loop]]:
    """
    Format:
      - First non-empty line: outer boundary "x1 y1 x2 y2 ..."
      - Subsequent non-empty lines: additional inner loops (holes/islands) in same format
    Returns: (exterior, [inner_loops...])
    """
    tic()
    lines: List[str] = []
    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if line:
                lines.append(line)
    if not lines:
        raise ValueError("No non-empty lines found")

    def parse_line(line: str) -> Loop:
        tokens = re.split(r"\s+", line.strip())
        pts = dedupe_closing_vertex(tokens_to_pairs(tokens))
        if len(pts) < 3:
            raise ValueError("Polygon has < 3 vertices")
        return pts

    exterior = parse_line(lines[0])
    inner_loops = [parse_line(ln) for ln in lines[1:]]

    # Basic sanity: ensure each inner loop lies within exterior by centroid
    for idx, loop in enumerate(inner_loops):
        c = polygon_centroid(loop)
        if not point_in_polygon(c, exterior):
            raise ValueError(f"Inner loop #{idx+1} centroid not inside exterior")
    toc(f"read {len(lines)} loops from {path}")
    return exterior, inner_loops


# ------------- Line overlay helpers (for ParaView) -------------


def build_point_lookup(
    points_xyz: np.ndarray, ndp: int = 12
) -> Dict[Tuple[float, float], int]:
    """Map rounded (x,y) -> point index."""
    lut = {}
    for i, (x, y, _) in enumerate(points_xyz):
        lut[(round(x, ndp), round(y, ndp))] = i
    return lut


def map_loop_to_node_ids(
    loop: Loop,
    points_xyz: np.ndarray,
    lut: Dict[Tuple[float, float], int],
    ndp: int = 12,
) -> List[int]:
    """Map exact loop vertices to nearest mesh vertices (fallback to nearest if rounding misses)."""
    ids: List[int] = []
    P2 = points_xyz[:, :2]
    for x, y in loop:
        key = (round(x, ndp), round(y, ndp))
        if key in lut:
            ids.append(lut[key])
        else:
            d2 = np.sum((P2 - np.array([x, y])) ** 2, axis=1)
            ids.append(int(np.argmin(d2)))
    return ids


# ------------- Nesting/metadata helpers -------------


def sample_point_inside(poly: Loop, eps: float = 1e-3) -> XY:
    """
    Return a point guaranteed to be inside 'poly' but biased toward a vertex,
    so it cannot lie inside an inner loop of 'poly' (for non-overlapping rings).
    """
    c = polygon_centroid(poly)
    v0x, v0y = poly[0]
    return (c[0] + (v0x - c[0]) * (1.0 - eps), c[1] + (v0y - c[1]) * (1.0 - eps))


def compute_loop_metadata(
    exterior: Loop, inner_loops: Optional[List[Loop]]
) -> List[Dict]:
    """
    Build list of loops with:
      poly, ccw, sample_pt (inside loop), depth (containers count)
    Depth is computed by counting how many OTHER loops contain the loop's *sample point*
    (near a vertex), which avoids misclassifying the outer loop when its centroid
    lies inside an inner ring.
    """
    loops: List[Dict] = [{"name": "outer", "poly": exterior}]
    for k, lp in enumerate(inner_loops or []):
        loops.append({"name": f"loop{k}", "poly": lp})

    for L in loops:
        L["ccw"] = signed_area(L["poly"]) > 0
        L["sample_pt"] = sample_point_inside(L["poly"])  # inside this loop

    for i, Li in enumerate(loops):
        depth = 0
        pt = Li["sample_pt"]
        for j, Lj in enumerate(loops):
            if j == i:
                continue
            if point_in_polygon(pt, Lj["poly"]):
                depth += 1
        Li["depth"] = depth
    return loops


# ------------- Core meshing (remove holes via even–odd parity) -------------


def mesh_polygon(
    exterior: Loop,
    inner_loops: Optional[List[Loop]] = None,
    *,
    maxh: float = 0.2,
    return_numpy: bool = False,
):
    """
    Mesh a polygon with arbitrary nesting using the even–odd rule:
      depth 0 (outer) and depth 2,4,... → inside domain = 1 (meshed)
      depth 1,3,... → inside domain = 0 (removed holes)

    Returns:
      ngmesh, (points_xyz, triangles, edges) if return_numpy=True
    """
    loops = compute_loop_metadata(exterior, inner_loops)

    if loops[0]["depth"] != 0:
        raise ValueError("Exterior loop appears nested; check input data")

    # Build Netgen geometry with left/right domains
    tic()
    geo = SplineGeometry()
    for L in loops:
        poly = L["poly"]
        desired_dom = 1 if (L["depth"] % 2 == 0) else 0
        ld_inside = int(desired_dom)
        rd_outside = 1 - ld_inside
        pids = [geo.AppendPoint(float(x), float(y)) for (x, y) in poly]
        for k in range(len(pids)):
            a = pids[k]
            b = pids[(k + 1) % len(pids)]
            if L["ccw"]:
                geo.Append(
                    ["line", a, b], leftdomain=ld_inside, rightdomain=rd_outside, bc=1
                )
            else:
                geo.Append(
                    ["line", a, b], leftdomain=rd_outside, rightdomain=ld_inside, bc=1
                )
    toc("geometry build")

    mp = make_mp_fast(maxh)

    tic()
    ngmesh = geo.GenerateMesh(mp)
    toc("mesh generation")

    if not return_numpy:
        return ngmesh

    points_xyz = np.array(
        [[p.p[0], p.p[1], p.p[2]] for p in ngmesh.Points()], dtype=np.float64
    )
    triangles = np.array(
        [[v.nr - 1 for v in el.vertices] for el in ngmesh.Elements2D()], dtype=np.int32
    )
    edges = np.array(
        [[v.nr - 1 for v in el.vertices] for el in ngmesh.Elements1D()], dtype=np.int32
    )
    return ngmesh, points_xyz, triangles, edges


# ------------- Core meshing (preserve inner contours as interfaces) -------------


def mesh_polygon_with_interfaces(
    exterior: Loop,
    inner_loops: Optional[List[Loop]] = None,
    *,
    maxh: float = 0.5,
    return_numpy: bool = True,
    add_interface_lines: bool = True,
    include_outer_lines: bool = False,
):
    """
    Build a multi-domain mesh where all nested regions are meshed,
    and each provided inner loop is kept as an internal interface.

    Strategy:
      - Assign inside domain by nesting depth parity: depth even → domain 1, depth odd → domain 2.
      - Outer loop has outside domain 0 (non-meshed); inner loops use the opposite domain outside,
        forcing the loop to become an interface.

    Returns:
      ngmesh, points_xyz, triangles, tri_regions, line_cells (optional)
    """
    loops = compute_loop_metadata(exterior, inner_loops)

    if loops[0]["depth"] != 0:
        raise ValueError("Exterior loop appears nested; check input data")

    # Build geometry with domains alternating 1/2
    tic()
    geo = SplineGeometry()
    for L in loops:
        poly = L["poly"]
        inside_dom = 1 if (L["depth"] % 2 == 0) else 2
        outside_dom = 0 if L is loops[0] else (2 if inside_dom == 1 else 1)
        pids = [geo.AppendPoint(float(x), float(y)) for (x, y) in poly]
        for k in range(len(pids)):
            a = pids[k]
            b = pids[(k + 1) % len(pids)]
            if L["ccw"]:
                geo.Append(
                    ["line", a, b],
                    leftdomain=int(inside_dom),
                    rightdomain=int(outside_dom),
                    bc=1,
                )
            else:
                geo.Append(
                    ["line", a, b],
                    leftdomain=int(outside_dom),
                    rightdomain=int(inside_dom),
                    bc=1,
                )
    toc("geometry build")

    mp = make_mp_fast(maxh)

    tic()
    ngmesh = geo.GenerateMesh(mp)
    dt = toc("mesh generation")

    # To NumPy
    tic()
    points_xyz = np.array(
        [[p.p[0], p.p[1], p.p[2]] for p in ngmesh.Points()], dtype=np.float64
    )
    triangles = np.array(
        [[v.nr - 1 for v in el.vertices] for el in ngmesh.Elements2D()], dtype=np.int32
    )
    toc("convert to NumPy")

    # Per-triangle region via centroid parity (matches domain assignment)
    # tic()
    # tri_regions = np.empty(len(triangles), dtype=np.int32)
    # loop_polys = [L["poly"] for L in loops]
    # for i, tri in enumerate(triangles):
    #    cx, cy = tri_centroid(points_xyz, tri)
    #    count = sum(1 for poly in loop_polys if point_in_polygon((cx, cy), poly))
    #    tri_regions[i] = 1 if (count % 2 == 1) else 2
    # toc("compute triangle regions")

    # Optional: add line cells along provided loops
    # tic()
    # line_cells = None
    # if add_interface_lines:
    #    lut = build_point_lookup(points_xyz)
    #    which = loops if include_outer_lines else loops[1:]
    #    lines: List[List[int]] = []
    #    for L in which:
    #        ids = map_loop_to_node_ids(L["poly"], points_xyz, lut)
    #        for k in range(len(ids)):
    #            lines.append([ids[k], ids[(k + 1) % len(ids)]])
    #    line_cells = np.array(lines, dtype=np.int32) if lines else None
    # toc("map loops to line cells")

    # Takes a long time
    tri_regions = np.empty(len(triangles), dtype=np.int32)
    line_cells = None

    if not return_numpy:
        return ngmesh

    return ngmesh, points_xyz, triangles, tri_regions, line_cells, dt


# ------------- VTU writers -------------


def save_vtu(
    points_xyz: np.ndarray,
    triangles: np.ndarray,
    edges: Optional[np.ndarray] = None,
    filename: str = "mesh.vtu",
) -> None:
    tic()
    cells = [("triangle", triangles)]
    if edges is not None and len(edges) > 0:
        cells.append(("line", edges))
    meshio.Mesh(points=points_xyz, cells=cells).write(filename)
    print(
        f"Saved {filename} (triangles={len(triangles)}, lines={0 if edges is None else len(edges)})"
    )
    toc(f"write {filename}")


def save_vtu_with_regions_and_lines(
    points_xyz: np.ndarray,
    triangles: np.ndarray,
    regions: np.ndarray,
    line_cells: Optional[np.ndarray] = None,
    filename: str = "mesh_regions.vtu",
) -> None:
    tic()
    cells = [("triangle", triangles)]
    cell_data = {"region": [regions]}
    if line_cells is not None and len(line_cells) > 0:
        cells.append(("line", line_cells))
        cell_data["region"].append(
            np.zeros(len(line_cells), dtype=np.int32)
        )  # pad for line block
    meshio.Mesh(points=points_xyz, cells=cells, cell_data=cell_data).write(filename)
    print(
        f"Saved {filename} (triangles={len(triangles)}, lines={0 if line_cells is None else len(line_cells)})"
    )
    toc(f"write {filename}")


# ------------- Test geometries -------------


def test_square(maxh: float = 0.2, fname: str = "square.vtu") -> None:
    verts = [(0, 0), (1, 0), (1, 1), (0, 1)]
    _, pts, tris, eds = mesh_polygon(
        verts, inner_loops=None, maxh=maxh, return_numpy=True
    )
    save_vtu(pts, tris, eds, fname)


def test_square_with_hole_interfaces(
    maxh: float = 0.2, fname: str = "square_interfaces.vtu"
) -> None:
    outer = [(0, 0), (3, 0), (3, 2), (0, 2)]
    hole = [(1, 0.5), (2, 0.5), (2, 1.5), (1, 1.5)]
    _, pts, tris, regions, lines, __ = mesh_polygon_with_interfaces(
        outer, [hole], maxh=maxh, return_numpy=True
    )
    save_vtu_with_regions_and_lines(pts, tris, regions, lines, fname)


def test_concave(maxh: float = 0.2, fname: str = "concave.vtu") -> None:
    verts = [(0, 0), (3, 0), (3, 2), (2, 2), (2, 1), (1, 1), (1, 2), (0, 2)]
    _, pts, tris, eds = mesh_polygon(verts, maxh=maxh, return_numpy=True)
    save_vtu(pts, tris, eds, fname)


def test_L_shape(maxh: float = 0.15, fname: str = "L_shape.vtu") -> None:
    verts = [(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)]
    _, pts, tris, eds = mesh_polygon(verts, maxh=maxh, return_numpy=True)
    save_vtu(pts, tris, eds, fname)


def read_loops_from_file_and_mesh_remove_holes(
    path: str = "testcase.txt", maxh: float = 100.0, fname: str = "gbg_removeholes.vtu"
) -> None:
    outer, loops = read_loops_from_file(path)
    _, pts, tris, eds = mesh_polygon(
        outer, inner_loops=loops, maxh=maxh, return_numpy=True
    )
    save_vtu(pts, tris, eds, fname)


def read_loops_from_file_and_mesh_interfaces(
    path: str = "testcase.txt", maxh: float = 100.0, fname: str = "gbg_interfaces.vtu"
) -> None:
    outer, loops = read_loops_from_file(path)
    _, pts, tris, regions, lines, dt = mesh_polygon_with_interfaces(
        outer, inner_loops=loops, maxh=maxh, return_numpy=True
    )
    save_vtu_with_regions_and_lines(pts, tris, regions, lines, fname)


def bench():

    import sys

    outer, loops = read_loops_from_file("testcase.txt")

    times = []
    cells = []

    mesh_sizes = [100.0, 10.0, 5.0, 2.0, 1.0, 0.5]
    for h in mesh_sizes:
        print(f"\nMeshing with maxh = {h}")
        _, pts, tris, regions, lines, dt = mesh_polygon_with_interfaces(
            outer, inner_loops=loops, maxh=h, return_numpy=True
        )
        times.append(dt)
        cells.append(len(tris))

    print()

    # Print results as a nice little table with h, #cells, time, cells/s
    print(f"{'maxh':>10} {'#cells':>10} {'time (s)':>10} {'cells/s':>10}")
    print("-" * 44)
    for h, n, t in zip(mesh_sizes, cells, times):
        rate = n / t if t > 0 else 0.0
        print(f"{h:10.3f} {n:10d} {t:10.3f} {rate:10.1f}")


# ------------- Main -------------

if __name__ == "__main__":
    print("Generating test meshes...")

    if "--bench" in sys.argv:
        bench()
        exit()

    test_square()
    test_square_with_hole_interfaces()
    test_concave()
    test_L_shape()
    read_loops_from_file_and_mesh_remove_holes()
    read_loops_from_file_and_mesh_interfaces()
    print(
        "Done. Open the .vtu files in ParaView (color by 'region' for *interfaces* cases)."
    )
