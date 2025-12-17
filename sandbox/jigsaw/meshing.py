from typing import List, Tuple, Optional, Dict
from pathlib import Path
import jigsawpy as jig
import numpy as np
import meshio

import re
import time
import sys

from utils import tic, toc,Loop,XY, point_in_polygon
from utils import (
    compute_loop_metadata,
    sample_point_inside,
    build_point_lookup,
    map_loop_to_node_ids,
)

from utils import (
    _segments_from_loops,
    _build_children_map,
    _region_id_for_point,
    _build_seeds_all_parts,
    _seed_inside_excluding_children,
)





def _build_edge_hfun_grid(
    exterior: Loop,
    inner_loops: Optional[List[Loop]],
    *,
    maxh: float,
    edge_hmin: Optional[float] = None,
    edge_band: Optional[float] = None,
    grid_n: int = 160,
) -> jig.jigsaw_msh_t:
    """Build a euclidean-grid HFUN that refines near input edges.

    H(x) = edge_hmin + (maxh - edge_hmin) * clip(dist(edge)/edge_band, 0, 1)
    """
    if edge_hmin is None:
        edge_hmin = max(0.1 * maxh, maxh * 0.25)
    if edge_band is None:
        edge_band = 3.0 * maxh

    loops = compute_loop_metadata(exterior, inner_loops)
    segs = _segments_from_loops(loops)  # (M,4)
    # Domain bounds from exterior
    xs, ys = zip(*exterior)
    xmin, xmax = float(min(xs)), float(max(xs))
    ymin, ymax = float(min(ys)), float(max(ys))

    # Grid resolution with safety clamp
    w = max(xmax - xmin, 1.0)
    h = max(ymax - ymin, 1.0)
    nx = max(32, min(grid_n, int(np.ceil(w / maxh)) * 4))
    ny = max(32, min(grid_n, int(np.ceil(h / maxh)) * 4))

    xg = np.linspace(xmin, xmax, nx)
    yg = np.linspace(ymin, ymax, ny)
    XX, YY = np.meshgrid(xg, yg)
    P = np.column_stack([XX.ravel(), YY.ravel()])  # (N,2)

    # Compute distance to nearest segment (vectorised over points; loop segs)
    mind2 = np.full(P.shape[0], np.inf, dtype=np.float64)
    for (x0, y0, x1, y1) in segs:
        vx = x1 - x0
        vy = y1 - y0
        denom = vx * vx + vy * vy + 1e-300
        wx = P[:, 0] - x0
        wy = P[:, 1] - y0
        t = (wx * vx + wy * vy) / denom
        t = np.clip(t, 0.0, 1.0)
        projx = x0 + t * vx
        projy = y0 + t * vy
        dx = P[:, 0] - projx
        dy = P[:, 1] - projy
        d2 = dx * dx + dy * dy
        mind2 = np.minimum(mind2, d2)

    dist = np.sqrt(mind2)
    ramp = np.clip(dist / float(edge_band), 0.0, 1.0)
    H = float(edge_hmin) + (float(maxh) - float(edge_hmin)) * ramp
    H = H.reshape(yg.size, xg.size).astype(np.float64)

    hfun = jig.jigsaw_msh_t()
    hfun.mshID = "euclidean-grid"
    hfun.ndims = +2
    hfun.xgrid = np.asarray(xg, dtype=hfun.REALS_t)
    hfun.ygrid = np.asarray(yg, dtype=hfun.REALS_t)
    hfun.value = np.asarray(H, dtype=hfun.REALS_t)
    return hfun





def mesh_polygon( 
    exterior: Loop,
    inner_loops: Optional[List[Loop]] = None,
    *,
    maxh: float = 0.2,
    return_numpy: bool = False,
    refine_edges: bool = True,
    edge_hmin: Optional[float] = 0.5,
    edge_band: Optional[float] = None,
):
    """
    Mesh a polygon with optional inner loops (holes) using JIGSAW.

    Uses an even–odd rule via region seeds:
      - Place a seed inside every loop with even nesting depth (0,2,4,...).
        This meshes the outer region and any islands inside holes, while
        keeping odd-depth loops as internal boundaries (holes).

    Returns:
      jmesh, (points_xyz, triangles, edges) if return_numpy=True
    """

    # Compute nesting metadata (depth, ccw) identical to netgen version
    loops = compute_loop_metadata(exterior, inner_loops)
    if loops[0]["depth"] != 0:
        raise ValueError("Exterior loop appears nested; check input data")

    # Build JIGSAW geometry: concatenate vertices & edges for all loops
    geom = jig.jigsaw_msh_t()
    geom.mshID = "euclidean-mesh"
    geom.ndims = +2

    all_verts: List[Tuple[float, float]] = []
    all_edges: List[Tuple[int, int]] = []

    for L in loops:
        poly = L["poly"]
        start_idx = len(all_verts)
        all_verts.extend(poly)
        n = len(poly)
        for k in range(n):
            a = start_idx + k
            b = start_idx + ((k + 1) % n)
            all_edges.append((a, b))

    # Structured arrays expected by JIGSAW
    geom.vert2 = np.array(
        [((float(x), float(y)), 0) for (x, y) in all_verts], dtype=geom.VERT2_t
    )
    geom.edge2 = np.array(
        [((int(i), int(j)), 0) for (i, j) in all_edges], dtype=geom.EDGE2_t
    )

    # Seeds select which enclosed "parts" to mesh: even-depth loops
    seed_pts: List[Tuple[float, float]] = [
        sample_point_inside(L["poly"]) for L in loops if (L["depth"] % 2) == 0
    ]
    if len(seed_pts) == 0:
        # Fallback: seed centroid of exterior
        seed_pts = [sample_point_inside(exterior)]
    geom.seed2 = np.array(
        [((float(x), float(y)), 0) for (x, y) in seed_pts], dtype=geom.VERT2_t
    )

    # Meshing options
    opts = jig.jigsaw_jig_t()
    opts.verbosity = 0
    opts.mesh_dims = +2
    opts.hfun_scal = "absolute"
    opts.hfun_hmax = float(maxh)
    opts.mesh_kern = "delfront"
    # Strengthen boundary/topology fidelity
    opts.mesh_top1 = True
    opts.mesh_top2 = True
    opts.mesh_eps1 = 0.10
    opts.mesh_eps2 = 0.33

    # Run JIGSAW via in-memory API
    jmesh = jig.jigsaw_msh_t()
    tic()
    if refine_edges:
        hfun = _build_edge_hfun_grid(
            exterior, inner_loops, maxh=maxh,
            edge_hmin=edge_hmin, edge_band=edge_band,
        )
        # Tighten global min to the local edge minimum
        opts.hfun_hmin = float(hfun.value.min())
        jig.lib.jigsaw(opts, geom, jmesh, None, hfun)
    else:
        jig.lib.jigsaw(opts, geom, jmesh)
    toc("JIGSAW mesh generation")

    if not return_numpy:
        return jmesh

    # Convert to NumPy arrays compatible with VTU writers
    pts2 = jmesh.vert2["coord"].astype(np.float64)
    points_xyz = np.column_stack([pts2, np.zeros((pts2.shape[0],), dtype=np.float64)])
    triangles = jmesh.tria3["index"].astype(np.int32)
    edges = jmesh.edge2["index"].astype(np.int32)

    return jmesh, points_xyz, triangles, edges

def mesh_polygon_with_interfaces(
    exterior: Loop,
    inner_loops: Optional[List[Loop]] = None,
    *,
    maxh: float = 0.5,
    return_numpy: bool = True,
    add_interface_lines: bool = True,
    include_outer_lines: bool = False,
    refine_edges: bool = True,
    edge_hmin: Optional[float] = None,
    edge_band: Optional[float] = None,
):
    """
    Build a multi-domain mesh preserving inner loops as interfaces using JIGSAW.

    Strategy:
      - Include all loops (outer + inner) as geometry edges.
      - Seed inside every loop (and the outer region) so both sides of each
        inner loop are meshed; the loop polylines remain as internal interfaces.

    Returns:
      jmesh, points_xyz, triangles, tri_regions, line_cells, dt
    """

    loops = compute_loop_metadata(exterior, inner_loops)
    if loops[0]["depth"] != 0:
        raise ValueError("Exterior loop appears nested; check input data")

    # Geometry assembly (concatenate vertices & edges per loop)
    geom = jig.jigsaw_msh_t()
    geom.mshID = "euclidean-mesh"
    geom.ndims = +2

    all_verts: List[Tuple[float, float]] = []
    all_edges: List[Tuple[int, int]] = []
    for L in loops:
        poly = L["poly"]
        start = len(all_verts)
        all_verts.extend(poly)
        n = len(poly)
        for k in range(n):
            a = start + k
            b = start + ((k + 1) % n)
            all_edges.append((a, b))

    geom.vert2 = np.array(
        [((float(x), float(y)), 0) for (x, y) in all_verts], dtype=geom.VERT2_t
    )
    geom.edge2 = np.array(
        [((int(i), int(j)), 0) for (i, j) in all_edges], dtype=geom.EDGE2_t
    )

    # Seeds: inside all loops; outer loop seed covers background ring region
    seeds: List[Tuple[float, float]] = [sample_point_inside(L["poly"]) for L in loops]
    if not seeds:
        seeds = [sample_point_inside(exterior)]
    geom.seed2 = np.array(
        [((float(x), float(y)), 0) for (x, y) in seeds], dtype=geom.VERT2_t
    )

    # Options and meshing
    opts = jig.jigsaw_jig_t()
    opts.verbosity = 0
    opts.mesh_dims = +2
    opts.hfun_scal = "absolute"
    opts.hfun_hmax = float(maxh)
    opts.mesh_top1 = True
    opts.mesh_top2 = True
    opts.mesh_eps1 = 0.10
    opts.mesh_eps2 = 0.33

    jmesh = jig.jigsaw_msh_t()
    tic()
    if refine_edges:
        hfun = _build_edge_hfun_grid(
            exterior, inner_loops, maxh=maxh,
            edge_hmin=edge_hmin, edge_band=edge_band,
        )
        opts.hfun_hmin = float(hfun.value.min())
        jig.lib.jigsaw(opts, geom, jmesh, None, hfun)
    else:
        jig.lib.jigsaw(opts, geom, jmesh)
    dt = toc("JIGSAW mesh generation (interfaces)")

    # Extract arrays
    pts2 = jmesh.vert2["coord"].astype(np.float64)
    points_xyz = np.column_stack([pts2, np.zeros((pts2.shape[0],), dtype=np.float64)])
    triangles = jmesh.tria3["index"].astype(np.int32)

    # Per-triangle region: unique id per subdomain (deepest container minus its children)
    tri_regions = np.empty(len(triangles), dtype=np.int32)
    children_map = _build_children_map(loops)
    for i, tri in enumerate(triangles):
        a, b, c = points_xyz[tri[0]], points_xyz[tri[1]], points_xyz[tri[2]]
        cx = (a[0] + b[0] + c[0]) / 3.0
        cy = (a[1] + b[1] + c[1]) / 3.0
        ridx = _region_id_for_point((cx, cy), loops, children_map)
        tri_regions[i] = (ridx + 1) if ridx >= 0 else 0

    # Optional overlay line-cells along the input loops
    line_cells = None
    if add_interface_lines:
        lut = build_point_lookup(points_xyz)
        which = loops if include_outer_lines else loops[1:]
        lines: List[List[int]] = []
        for L in which:
            ids = map_loop_to_node_ids(L["poly"], points_xyz, lut)
            for k in range(len(ids)):
                lines.append([ids[k], ids[(k + 1) % len(ids)]])
        line_cells = np.array(lines, dtype=np.int32) if lines else None

    if not return_numpy:
        return jmesh

    return jmesh, points_xyz, triangles, tri_regions, line_cells, dt


def mesh_polygon_fill(
    exterior: Loop,
    inner_loops: Optional[List[Loop]] = None,
    *,
    maxh: float = 0.2,
    return_numpy: bool = False,
    refine_edges: bool = True,
    edge_hmin: Optional[float] = None,
    edge_band: Optional[float] = None,
    debug_dump_seeds: bool = True,
    debug_seeds_path: Optional[str] = "seeds.vtu",
):
    """
    Mesh a polygon where inner loops are NOT holes but triangulated as
    interior subdomains, with their edges strictly respected.

    Returns the same tuple shape as mesh_polygon_with_interfaces:
      jmesh, points_xyz, triangles, tri_regions, line_cells, dt
    """

    loops = compute_loop_metadata(exterior, inner_loops)
    if loops[0]["depth"] != 0:
        raise ValueError("Exterior loop appears nested; check input data")

    # Geometry: all loops as constrained edges
    geom = jig.jigsaw_msh_t()
    geom.mshID = "euclidean-mesh"
    geom.ndims = +2

    all_verts: List[Tuple[float, float]] = []
    all_edges: List[Tuple[int, int]] = []
    for L in loops:
        poly = L["poly"]
        s = len(all_verts)
        all_verts.extend(poly)
        n = len(poly)
        for k in range(n):
            a = s + k
            b = s + ((k + 1) % n)
            all_edges.append((a, b))
    
    geom.vert2 = np.array(
        [((float(x), float(y)), 0) for (x, y) in all_verts], dtype=geom.VERT2_t
    )
    geom.edge2 = np.array(
        [((int(i), int(j)), 0) for (i, j) in all_edges], dtype=geom.EDGE2_t
    )

    # Seeds in every loop (outer + inner), chosen outside any immediate children
    seeds: List[Tuple[float, float]] = _build_seeds_all_parts(loops)
    geom.seed2 = np.array(
        [((float(x), float(y)), 0) for (x, y) in seeds], dtype=geom.VERT2_t
    )

    # Optional debug: write seeds to VTU to verify coverage
    if debug_dump_seeds:
        seeds_xyz = np.column_stack([np.asarray(seeds, dtype=np.float64), np.zeros((len(seeds),), dtype=np.float64)])
        out = debug_seeds_path or "seeds.vtu"
        meshio.Mesh(points=seeds_xyz, cells=[]).write(out)

    # for L, s in zip(loops, seeds):
    #     if not point_in_polygon(s, L["poly"]):
    #         print("Warning: seed not in loop?", L["name"], s, file=sys.stderr)
    #     print(f"  Loop '{L['name']}' depth={L['depth']} ccw={L['ccw']} seed={s}")

    # Options
    opts = jig.jigsaw_jig_t()
    opts.verbosity = 0
    opts.mesh_dims = +2
    opts.hfun_scal = "absolute"
    opts.hfun_hmax = float(maxh)
    # Preserve and respect embedded interfaces
    opts.mesh_kern = "delfront"
    opts.bnds_kern = "triacell"
    # Strong edge/face conformance
    opts.mesh_top1 = True
    opts.mesh_top2 = True
    opts.mesh_eps1 = 0.10
    opts.mesh_eps2 = 0.33
    opts.mesh_lock = True
    # encourage detection of sharp corners on polyline chains
    opts.geom_feat = True

    # Meshing
    jmesh = jig.jigsaw_msh_t()
    tic()
    if refine_edges:
        hfun = _build_edge_hfun_grid(
            exterior, inner_loops, maxh=maxh,
            edge_hmin=edge_hmin, edge_band=edge_band,
        )
        opts.hfun_hmin = float(hfun.value.min())
        jig.lib.jigsaw(opts, geom, jmesh, None, hfun)
    else:
        jig.lib.jigsaw(opts, geom, jmesh)
    dt = toc("JIGSAW mesh generation (filled)")

    if not return_numpy:
        return jmesh

    pts2 = jmesh.vert2["coord"].astype(np.float64)
    points_xyz = np.column_stack([pts2, np.zeros((pts2.shape[0],), dtype=np.float64)])
    triangles = jmesh.tria3["index"].astype(np.int32)

    # Regions: unique id per subdomain
    tri_regions = np.empty(len(triangles), dtype=np.int32)
    children_map = _build_children_map(loops)
    for i, tri in enumerate(triangles):
        a, b, c = points_xyz[tri[0]], points_xyz[tri[1]], points_xyz[tri[2]]
        cx = (a[0] + b[0] + c[0]) / 3.0
        cy = (a[1] + b[1] + c[1]) / 3.0
        ridx = _region_id_for_point((cx, cy), loops, children_map)
        tri_regions[i] = (ridx + 1) if ridx >= 0 else 0

    # Polyline overlays along inner loops
    lut = build_point_lookup(points_xyz)
    which = loops[1:] if len(loops) > 1 else []
    lines: List[List[int]] = []
    for L in which:
        ids = map_loop_to_node_ids(L["poly"], points_xyz, lut)
        for k in range(len(ids)):
            lines.append([ids[k], ids[(k + 1) % len(ids)]])
    line_cells = np.array(lines, dtype=np.int32) if lines else None

    return jmesh, points_xyz, triangles, tri_regions, line_cells, dt



def mesh_polygon_bound(
    exterior: Loop,
    inner_loops: Optional[List[Loop]] = None,
    *,
    maxh: float = 0.2,
    return_numpy: bool = False,
    refine_edges: bool = True,
    edge_hmin: Optional[float] = None,
    edge_band: Optional[float] = None,
    verbosity: int = 0,
    debug_dump_seeds: bool = False,
    debug_seeds_path: Optional[str] = "seeds_bound.vtu",
    ):

    # Compute nesting/depth metadata
    loops = compute_loop_metadata(exterior, inner_loops)
    if loops[0]["depth"] != 0:
        raise ValueError("Exterior loop appears nested; check input data")

    # Helper: immediate children indices per loop
    children_map = _build_children_map(loops)

    # Geometry assembly (concatenate vertices & edges per loop)
    geom = jig.jigsaw_msh_t()
    geom.mshID = "euclidean-mesh"
    geom.ndims = +2

    all_verts: List[Tuple[float, float]] = []
    all_edges: List[Tuple[int, int]] = []
    loop_edge_ids: List[List[int]] = []  # per-loop list of edge indices

    for L in loops:
        poly = L["poly"]
        s = len(all_verts)
        all_verts.extend(poly)
        n = len(poly)
        edges_for_loop: List[int] = []
        for k in range(n):
            a = s + k
            b = s + ((k + 1) % n)
            edges_for_loop.append(len(all_edges))
            all_edges.append((a, b))
        loop_edge_ids.append(edges_for_loop)

    geom.vert2 = np.array(
        [((float(x), float(y)), 0) for (x, y) in all_verts], dtype=geom.VERT2_t
    )
    geom.edge2 = np.array(
        [((int(i), int(j)), 0) for (i, j) in all_edges], dtype=geom.EDGE2_t
    )

    # Part-id assignment following terrain style
    # part 1 = background (outer loop)
    # one loop → one part-id
    loop_to_part: Dict[int, int] = {i: i + 1 for i in range(len(loops))}
    # (outer loop gets id=1, first inner gets id=2, etc.)

    # Seeds per distinct part-id, avoiding immediate children
    seeds_by_part: Dict[int, Tuple[float, float]] = {}

    # Seed for background (outer), choose a point not in immediate depth-1 holes
    outer_children = [loops[j]["poly"] for j in children_map[0]]
    seeds_by_part[1] = _seed_inside_excluding_children(loops[0]["poly"], outer_children)

    # Seeds for even-depth loops (>=2)
    seeds_by_part: Dict[int, Tuple[float, float]] = {}
    for i in range(len(loops)):
        # avoid placing the seed inside immediate children
        ch = [loops[j]["poly"] for j in children_map[i]]
        pid = loop_to_part[i]
        seeds_by_part[pid] = _seed_inside_excluding_children(loops[i]["poly"], ch)


    # Write seeds into geometry with part-id in IDtag
    if seeds_by_part:
        seed_arr = np.zeros(len(seeds_by_part), dtype=geom.VERT2_t)
        for idx, (pid, (sx, sy)) in enumerate(sorted(seeds_by_part.items())):
            seed_arr[idx]["coord"] = (float(sx), float(sy))
            seed_arr[idx]["IDtag"] = int(pid)
        geom.seed2 = seed_arr

    # Bound entries mapping each edge to its part-id
    bound_entries: List[Tuple[int, int, int]] = []
    for i, edge_ids in enumerate(loop_edge_ids):
        pid = loop_to_part[i]
        for eid in edge_ids:
            bound_entries.append((int(pid), int(eid), jig.jigsaw_def_t.JIGSAW_EDGE2_TAG))


    if bound_entries:
        geom.bound = np.array(bound_entries, dtype=geom.BOUND_t)

    # Options (strong edge/face conformance; lock interface constraints)
    opts = jig.jigsaw_jig_t()
    opts.verbosity = verbosity
    opts.mesh_dims = 2
    opts.hfun_scal = "absolute"
    opts.hfun_hmax = float(maxh)
    opts.mesh_kern = "delfront"
    opts.bnds_kern = "triacell"
    opts.mesh_top1 = True
    opts.mesh_top2 = True
    opts.mesh_eps1 = 0.10
    opts.mesh_eps2 = 0.33
    opts.mesh_lock = True
    opts.geom_feat = True
    opts.numthread = -1

    # Meshing
    jmesh = jig.jigsaw_msh_t()
    tic()
    if refine_edges:
        hfun = _build_edge_hfun_grid(
            exterior, inner_loops, maxh=maxh,
            edge_hmin=edge_hmin, edge_band=edge_band,
        )
        opts.hfun_hmin = float(hfun.value.min())
        jig.lib.jigsaw(opts, geom, jmesh, None, hfun)
    else:
        jig.lib.jigsaw(opts, geom, jmesh)
    dt = toc("JIGSAW mesh generation (bound)")

    if not return_numpy:
        return jmesh
    
    # Extract arrays
    pts2 = jmesh.vert2["coord"].astype(np.float64)
    points_xyz = np.column_stack([pts2, np.zeros((pts2.shape[0],), dtype=np.float64)])
    triangles = jmesh.tria3["index"].astype(np.int32)

    # Assign region for each triangle based on part mapping:
    # - find deepest container loop for centroid
    # - region = loop_to_part[that loop] (odd-depth maps to background id=1)
    order = sorted(range(len(loops)), key=lambda i: loops[i]["depth"], reverse=True)
    tri_regions = np.empty(len(triangles), dtype=np.int32)
    for i, tri in enumerate(triangles):
        a, b, c = points_xyz[tri[0]], points_xyz[tri[1]], points_xyz[tri[2]]
        cx = (a[0] + b[0] + c[0]) / 3.0
        cy = (a[1] + b[1] + c[1]) / 3.0
        rid = 0
        for idx in order:
            if point_in_polygon((cx, cy), loops[idx]["poly"]):
                rid = int(loop_to_part[idx])
                break
        tri_regions[i] = rid

    # Polyline overlays along inner loops
    lut = build_point_lookup(points_xyz)
    which = loops[1:] if len(loops) > 1 else []
    lines: List[List[int]] = []
    for L in which:
        ids = map_loop_to_node_ids(L["poly"], points_xyz, lut)
        for k in range(len(ids)):
            lines.append([ids[k], ids[(k + 1) % len(ids)]])
    line_cells = np.array(lines, dtype=np.int32) if lines else None

    # Optional debug: dump seeds
    if debug_dump_seeds and seeds_by_part:
        seeds = np.array([[sx, sy] for (_, (sx, sy)) in sorted(seeds_by_part.items())], dtype=np.float64)
        seeds_xyz = np.column_stack([seeds, np.zeros((len(seeds),), dtype=np.float64)])
        meshio.Mesh(points=seeds_xyz, cells=[]).write(debug_seeds_path or "seeds_bound.vtu")

    return jmesh, points_xyz, triangles, tri_regions, line_cells, dt
