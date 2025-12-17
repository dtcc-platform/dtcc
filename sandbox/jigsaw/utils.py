from typing import List, Tuple, Optional, Dict
import time 
import re
import meshio
import numpy as np

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


# ------------- Types -------------
XY = Tuple[float, float]
Loop = List[XY]


# ------------- Geometry Helpers -------------
def _segments_from_loops(loops: List[Dict]) -> np.ndarray:
    segs = []
    for L in loops:
        poly = L["poly"]
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % n]
            segs.append((float(x0), float(y0), float(x1), float(y1)))
    return np.asarray(segs, dtype=np.float64)

def _contains_any(pt: Tuple[float, float], polys: List[Loop]) -> bool:
    for poly in polys:
        if point_in_polygon(pt, poly):
            return True
    return False


def _seed_inside_excluding_children(parent: Loop, children: List[Loop]) -> Tuple[float, float]:
    """Find a point guaranteed inside parent but not inside any of the children.

    Tries a sequence of heuristics and falls back to a coarse bbox search.
    """
    # 1) try biased samples along vertex->centroid directions
    c = polygon_centroid(parent)
    for eps in (1e-3, 5e-2, 1.5e-1, 3.5e-1):
        s = (c[0] + (parent[0][0] - c[0]) * (1.0 - eps),
             c[1] + (parent[0][1] - c[1]) * (1.0 - eps))
        if point_in_polygon(s, parent) and not _contains_any(s, children):
            return s
    # 2) try along a few vertex rays
    for vidx in (0, 1, 2, 3) if len(parent) >= 4 else range(len(parent)):
        vx, vy = parent[vidx]
        for t in (0.2, 0.4, 0.6, 0.8):
            s = (vx * (1.0 - t) + c[0] * t, vy * (1.0 - t) + c[1] * t)
            if point_in_polygon(s, parent) and not _contains_any(s, children):
                return s
    # 3) centroid itself
    if point_in_polygon(c, parent) and not _contains_any(c, children):
        return c
    # 4) coarse bbox grid search
    xs, ys = zip(*parent)
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    nx = ny = 16
    for i in range(nx):
        x = xmin + (i + 0.5) / nx * (xmax - xmin)
        for j in range(ny):
            y = ymin + (j + 0.5) / ny * (ymax - ymin)
            s = (x, y)
            if point_in_polygon(s, parent) and not _contains_any(s, children):
                return s
    # 5) last resort: first vertex nudged towards centroid
    vx, vy = parent[0]
    s = (0.9 * vx + 0.1 * c[0], 0.9 * vy + 0.1 * c[1])
    return s


def _build_seeds_all_parts(loops: List[Dict]) -> List[Tuple[float, float]]:
    """Return one seed per loop, guaranteed to be in the loop but outside its children.

    This ensures all annular regions between nested loops are also meshed
    (parent seeds sit outside all immediate children).
    """
    seeds: List[Tuple[float, float]] = []
    # Pre-compute children per loop (immediate nesting: depth+1 and contained)
    for i, Li in enumerate(loops):
        parent_poly = Li["poly"]
        parent_depth = Li["depth"]
        children = []
        for j, Lj in enumerate(loops):
            if j == i:
                continue
            if Lj["depth"] == parent_depth + 1 and point_in_polygon(polygon_centroid(Lj["poly"]), parent_poly):
                children.append(Lj["poly"])
        seeds.append(_seed_inside_excluding_children(parent_poly, children))
    return seeds


def _build_children_map(loops: List[Dict]) -> List[List[int]]:
    """Immediate children per loop based on depth and containment."""
    children_map: List[List[int]] = [[] for _ in loops]
    for i, Li in enumerate(loops):
        dep_i = Li["depth"]
        poly_i = Li["poly"]
        for j, Lj in enumerate(loops):
            if j == i:
                continue
            if Lj["depth"] == dep_i + 1 and point_in_polygon(polygon_centroid(Lj["poly"]), poly_i):
                children_map[i].append(j)
    return children_map


def _region_id_for_point(pt: Tuple[float, float], loops: List[Dict], children_map: List[List[int]]) -> int:
    """Assign a unique region-id: deepest loop that contains pt and none of its immediate children do.

    Returns the loop index (0..L-1) or -1 if outside all.
    """
    order = sorted(range(len(loops)), key=lambda i: loops[i]["depth"], reverse=True)
    for i in order:
        if point_in_polygon(pt, loops[i]["poly"]):
            good = True
            for cj in children_map[i]:
                if point_in_polygon(pt, loops[cj]["poly"]):
                    good = False
                    break
            if good:
                return i
    return -1

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
