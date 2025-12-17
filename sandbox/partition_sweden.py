import pickle
import numpy as np
import matplotlib.pyplot as plt
import pymetis
from shapely.geometry import box, LineString
from shapely.strtree import STRtree
from shapely.ops import unary_union, polygonize
from math import ceil

DOWNLOAD_DATA = True
X0 = 319995.962899
Y0 = 6399009.716755
L = 1000.0  # Size of bounding box
H = 200.0  # Root grid target size
M = 2.0  # Margin for building bounding boxes
MAX_DEPTH = 5  # Quadtree refinement depth (refines size by 2**MAX_DEPTH)
MIN_WORLD = M
K_PARTS = 16  # Number of partitions
PLOT_QUADTREE = True
PLOT_POLYGONS = True
PLOT_FOOTPRINTS = True
PLOT_BBOXES = False

# -----------------------------
# Data IO / Preprocessing
# -----------------------------


def load_footprints():
    if DOWNLOAD_DATA:
        import dtcc

        bounds = dtcc.Bounds(
            X0 - 0.5 * L, Y0 - 0.5 * L, X0 + 0.5 * L, Y0 + 0.5 * L, 0, 0
        )
        buildings = dtcc.download_footprints(bounds=bounds)
        footprints = []
        for b in buildings:
            xy = b.get_footprint().to_polygon().exterior.coords.xy
            vs = [(x, y) for (x, y) in zip(xy[0], xy[1])]
            footprints.append(vs)
        with open("footprints.pkl", "wb") as f:
            pickle.dump(footprints, f)
    else:
        with open("footprints.pkl", "rb") as f:
            footprints = pickle.load(f)

    footprints = [np.array(vs) for vs in footprints]

    # Normalize to origin
    x0 = min(vs[:, 0].min() for vs in footprints)
    y0 = min(vs[:, 1].min() for vs in footprints)
    for i in range(len(footprints)):
        footprints[i][:, 0] -= x0
        footprints[i][:, 1] -= y0

    # Set bounds
    x0 = 0.0
    y0 = 0.0
    x1 = max(vs[:, 0].max() for vs in footprints)
    y1 = max(vs[:, 1].max() for vs in footprints)
    bounds = (x0, y0, x1, y1)
    return footprints, bounds


def build_bboxes(footprints, margin=M):
    boxes = []
    for vs in footprints:
        x_min = vs[:, 0].min() - margin
        x_max = vs[:, 0].max() + margin
        y_min = vs[:, 1].min() - margin
        y_max = vs[:, 1].max()
        b = np.array(
            [
                [x_min, y_min],
                [x_max, y_min],
                [x_max, y_max],
                [x_min, y_max],
                [x_min, y_min],
            ]
        )
        boxes.append(b)
    return boxes


# -----------------------------
# Uniform grid (root cells)
# -----------------------------


def build_grid(x0, y0, x1, y1, h):
    Lx, Ly = x1 - x0, y1 - y0
    nx = int(ceil(Lx / h))
    ny = int(ceil(Ly / h))
    dx = Lx / nx
    dy = Ly / ny
    x_edges = x0 + np.arange(nx + 1) * dx
    y_edges = y0 + np.arange(ny + 1) * dy
    grid = np.empty((nx, ny, 4), dtype=np.float64)
    for i in range(nx):
        for j in range(ny):
            grid[i, j, 0] = x_edges[i]
            grid[i, j, 1] = y_edges[j]
            grid[i, j, 2] = x_edges[i + 1]
            grid[i, j, 3] = y_edges[j + 1]
    return grid


# -----------------------------
# Quadtree on an integer lattice
# -----------------------------


def setup_lattice(bounds, h, max_depth):
    x0, y0, x1, y1 = bounds
    Lx, Ly = x1 - x0, y1 - y0
    nx = int(ceil(Lx / h))
    ny = int(ceil(Ly / h))
    dx0 = Lx / nx
    dy0 = Ly / ny
    scale = 2**max_depth
    dx = dx0 / scale
    dy = dy0 / scale
    return {
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
        "nx": nx,
        "ny": ny,
        "dx0": dx0,
        "dy0": dy0,
        "dx": dx,
        "dy": dy,
        "scale": scale,
    }


def cell_world_bbox(lat, i0, j0, s):
    # Convert integer-lattice cell to world bbox
    x0 = lat["x0"] + i0 * lat["dx"]
    y0 = lat["y0"] + j0 * lat["dy"]
    x1 = x0 + s * lat["dx"]
    y1 = y0 + s * lat["dy"]
    return x0, y0, x1, y1


def quadtree_refine_cells(bboxes, bounds, h, max_depth, min_world=None):
    # Build STRtree over building bboxes
    bb_geoms = [
        box(b[:, 0].min(), b[:, 1].min(), b[:, 0].max(), b[:, 1].max()) for b in bboxes
    ]
    tree = STRtree(bb_geoms)

    # Setup lattice
    lat = setup_lattice(bounds, h, max_depth)

    # Initialize root cells
    s_root = lat["scale"]
    roots = [
        (i * s_root, j * s_root, s_root, 0)
        for i in range(lat["nx"])
        for j in range(lat["ny"])
    ]

    free_leaves = []
    blocked_leaves = []

    if min_world is None:
        min_world = 0.0

    stack = roots
    while stack:
        i0, j0, s, level = stack.pop()
        x0, y0, x1, y1 = cell_world_bbox(lat, i0, j0, s)
        g = box(x0, y0, x1, y1)

        # Query intersections
        hits = tree.query(g, predicate="intersects")
        has_hits = (hits.size > 0) if hasattr(hits, "size") else (len(hits) > 0)

        if not has_hits:
            free_leaves.append((i0, j0, s))
            continue

        too_small = (s * lat["dx"] <= min_world) or (s * lat["dy"] <= min_world)
        if level >= max_depth or too_small:
            blocked_leaves.append((i0, j0, s))
            continue

        hs = s // 2
        level1 = level + 1
        stack.append((i0, j0, hs, level1))
        stack.append((i0 + hs, j0, hs, level1))
        stack.append((i0, j0 + hs, hs, level1))
        stack.append((i0 + hs, j0 + hs, hs, level1))

    return lat, free_leaves, blocked_leaves


# -----------------------------
# Edge maps, adjacency, partitioning
# -----------------------------


def build_edge_map(leaves):
    # Horizontal unit segment key: ('h', y, x)
    # Vertical unit segment key:   ('v', x, y)
    edges = {}
    for cid, (i0, j0, s) in enumerate(leaves):
        yb = j0
        yt = j0 + s
        for x in range(i0, i0 + s):
            edges.setdefault(("h", yb, x), []).append(cid)
            edges.setdefault(("h", yt, x), []).append(cid)
        xl = i0
        xr = i0 + s
        for y in range(j0, j0 + s):
            edges.setdefault(("v", xl, y), []).append(cid)
            edges.setdefault(("v", xr, y), []).append(cid)
    return edges


def build_adjacency_from_edges(leaves, edge_map):
    adj = {cid: set() for cid in range(len(leaves))}
    for owners in edge_map.values():
        if len(owners) >= 2:
            for a in owners:
                for b in owners:
                    if a != b:
                        adj[a].add(b)
    adj = {k: sorted(list(v)) for k, v in adj.items()}
    return adj


def cell_center(lat, i0, j0, s):
    x0, y0, x1, y1 = cell_world_bbox(lat, i0, j0, s)
    return 0.5 * (x0 + x1), 0.5 * (y0 + y1)


def build_graph_arrays(leaves, adjacency, lat):
    # Build centers and integer weights (area proxy)
    centers = []
    vweights = []
    for cid, (i0, j0, s) in enumerate(leaves):
        cx, cy = cell_center(lat, i0, j0, s)
        centers.append((cx, cy))
        area = (s * lat["dx"]) * (s * lat["dy"])
        vweights.append(area)
    w = np.array(vweights, dtype=np.float64)
    w = w / (w.mean() + 1e-12)
    w = np.clip(np.round(w * 10), 1, 1000).astype(np.int32)
    adj = [adjacency[cid] for cid in range(len(leaves))]
    return centers, w, adj, np.array(vweights, dtype=np.float64)


def partition_graph(adj, vweights, k):
    _, labels = pymetis.part_graph(k, adjacency=adj, vweights=vweights.tolist())
    return np.array(labels, dtype=np.int32)


# -----------------------------
# Holes (blocked leaves) assignment
# -----------------------------


def blocked_components(blocked_leaves, blocked_edges):
    adj = {cid: set() for cid in range(len(blocked_leaves))}
    for owners in blocked_edges.values():
        if len(owners) >= 2:
            for a in owners:
                for b in owners:
                    if a != b:
                        adj[a].add(b)
    comps, seen = [], set()
    for u in range(len(blocked_leaves)):
        if u in seen:
            continue
        q = [u]
        seen.add(u)
        comp = []
        while q:
            v = q.pop()
            comp.append(v)
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    q.append(w)
        comps.append(comp)
    return comps


def assign_holes_to_partitions(
    blocked_leaves,
    blocked_edges,
    free_edges,
    free_labels,
    free_weights,
    k,
    lat,
    load_penalty=0.0,
):
    loads = np.zeros(k, dtype=float)
    for cid, lab in enumerate(free_labels):
        loads[lab] += free_weights[cid]
    target = loads.sum() / k

    # Map unit edge -> list of partition labels of free cells touching it
    edge_to_partlabels = {
        key: [free_labels[cid] for cid in owners] for key, owners in free_edges.items()
    }

    comps = blocked_components(blocked_leaves, blocked_edges)
    blocked_labels = np.full(len(blocked_leaves), -1, dtype=int)

    for comp in comps:
        contact = np.zeros(k, dtype=float)
        comp_area = 0.0

        for bcid in comp:
            i0, j0, s = blocked_leaves[bcid]
            comp_area += (s * lat["dx"]) * (s * lat["dy"])
            yb, yt = j0, j0 + s
            for x in range(i0, i0 + s):
                for key in (("h", yb, x), ("h", yt, x)):
                    if key in edge_to_partlabels:
                        for plab in edge_to_partlabels[key]:
                            contact[plab] += lat["dx"]
            xl, xr = i0, i0 + s
            for y in range(j0, j0 + s):
                for key in (("v", xl, y), ("v", xr, y)):
                    if key in edge_to_partlabels:
                        for plab in edge_to_partlabels[key]:
                            contact[plab] += lat["dy"]

        scores = contact.copy()
        if load_penalty > 0:
            scores -= load_penalty * np.maximum(0.0, loads - target)
        choice = int(np.argmax(scores))
        for bcid in comp:
            blocked_labels[bcid] = choice
        loads[choice] += comp_area

    return blocked_labels


# -----------------------------
# Coverage polygons as numpy arrays (hole-free faces)
# -----------------------------


def leaf_box(lat, i0, j0, s):
    x0, y0, x1, y1 = cell_world_bbox(lat, i0, j0, s)
    return box(x0, y0, x1, y1)


def build_coverage_polygons_np(
    free_leaves, free_labels, blocked_leaves, blocked_labels, k, lat
):
    # Build global boundary unit edges: interface edges + outer boundary
    from collections import defaultdict

    edge_count = defaultdict(int)
    edge_parts = defaultdict(set)

    def add_cell_edges(i0, j0, s, p):
        yb, yt = j0, j0 + s
        for x in range(i0, i0 + s):
            key = ("h", yb, x)
            edge_count[key] += 1
            edge_parts[key].add(p)
            key = ("h", yt, x)
            edge_count[key] += 1
            edge_parts[key].add(p)
        xl, xr = i0, i0 + s
        for y in range(j0, j0 + s):
            key = ("v", xl, y)
            edge_count[key] += 1
            edge_parts[key].add(p)
            key = ("v", xr, y)
            edge_count[key] += 1
            edge_parts[key].add(p)

    for cid, (i0, j0, s) in enumerate(free_leaves):
        add_cell_edges(i0, j0, s, int(free_labels[cid]))
    for bid, (i0, j0, s) in enumerate(blocked_leaves):
        add_cell_edges(i0, j0, s, int(blocked_labels[bid]))

    boundary_keys = [
        k for k in edge_count if edge_count[k] == 1 or len(edge_parts[k]) >= 2
    ]

    # Build integer lattice linework
    lines = []
    for kind, a, b in boundary_keys:
        if kind == "h":
            lines.append(LineString([(b, a), (b + 1, a)]))
        else:
            lines.append(LineString([(a, b), (a, b + 1)]))

    # Polygonize to faces (hole-free)
    merged = unary_union(lines)
    faces_int = list(polygonize(merged))

    # Build spatial index of cell boxes with labels for face labeling
    all_boxes = []
    all_labels = []
    for cid, leaf in enumerate(free_leaves):
        all_boxes.append(leaf_box(lat, *leaf))
        all_labels.append(int(free_labels[cid]))
    for bid, leaf in enumerate(blocked_leaves):
        all_boxes.append(leaf_box(lat, *leaf))
        all_labels.append(int(blocked_labels[bid]))
    tree = STRtree(all_boxes)

    # Convert faces to world coords and group by partition label (as numpy arrays of exterior)
    parts_np = [[] for _ in range(k)]
    for poly in faces_int:
        # Scale/translate to world coords
        ex = np.asarray(poly.exterior.coords, dtype=np.float64)
        ex[:, 0] = lat["x0"] + ex[:, 0] * lat["dx"]
        ex[:, 1] = lat["y0"] + ex[:, 1] * lat["dy"]

        # Label by representative point
        rep = poly.representative_point()
        rep_world_x = lat["x0"] + rep.x * lat["dx"]
        rep_world_y = lat["y0"] + rep.y * lat["dy"]
        rep_world = box(
            rep_world_x, rep_world_y, rep_world_x, rep_world_y
        ).centroid  # point geom

        idxs = tree.query(rep_world)
        label = None
        for idx in idxs:
            if all_boxes[idx].covers(rep_world):
                label = all_labels[idx]
                break
        if label is None:
            # Fallback: nearest box label
            if len(idxs) > 0:
                dists = [
                    (all_boxes[idx].distance(rep_world), all_labels[idx])
                    for idx in idxs
                ]
                dists.sort(key=lambda t: t[0])
                label = dists[0][1]
            else:
                label = 0
        parts_np[label].append(ex)

    return parts_np


# -----------------------------
# Plotting
# -----------------------------


def plot_footprints(footprints):
    for vs in footprints:
        xs = [v[0] for v in vs]
        ys = [v[1] for v in vs]
        plt.fill(xs, ys, color="lightgray", edgecolor="black", linewidth=0.5, zorder=3)
    plt.axis("equal")


def plot_bboxes(boxes):
    for b in boxes:
        xs = [v[0] for v in b]
        ys = [v[1] for v in b]
        plt.plot(xs, ys, color="black", linewidth=0.6, alpha=0.5, zorder=2)
    plt.axis("equal")


def plot_partitions_cells(
    free_leaves,
    lat,
    labels,
    blocked_leaves=None,
    blocked_labels=None,
    cmap_name="tab20",
):
    cmap = plt.get_cmap(cmap_name)
    for cid, (i0, j0, s) in enumerate(free_leaves):
        x0, y0, x1, y1 = cell_world_bbox(lat, i0, j0, s)
        xs = [x0, x1, x1, x0, x0]
        ys = [y0, y0, y1, y1, y0]
        c = cmap((labels[cid] % 20) / 20.0)
        plt.fill(
            xs, ys, color=c, alpha=0.35, linewidth=0.4, edgecolor="black", zorder=1
        )
    if blocked_leaves is not None and blocked_labels is not None:
        for bid, (i0, j0, s) in enumerate(blocked_leaves):
            x0, y0, x1, y1 = cell_world_bbox(lat, i0, j0, s)
            xs = [x0, x1, x1, x0, x0]
            ys = [y0, y0, y1, y1, y0]
            c = cmap((blocked_labels[bid] % 20) / 20.0)
            plt.fill(
                xs, ys, color=c, alpha=0.20, linewidth=0.3, edgecolor="black", zorder=1
            )
    plt.axis("equal")


def plot_partition_polygons_np(part_polys_np, cmap_name="tab20"):
    cmap = plt.get_cmap(cmap_name)
    for pid, polys in enumerate(part_polys_np):
        for arr in polys:
            c = cmap((pid % 20) / 20.0)
            plt.fill(
                arr[:, 0],
                arr[:, 1],
                color=c,
                alpha=0.35,
                edgecolor="black",
                linewidth=1.0,
                zorder=1,
            )
    plt.axis("equal")


# -----------------------------
# Main
# -----------------------------

# Load footprints and bboxes
footprints, bounds = load_footprints()
bboxes = build_bboxes(footprints)

# Build quadtree leaves
lat, free_leaves, blocked_leaves = quadtree_refine_cells(
    bboxes=bboxes, bounds=bounds, h=H, max_depth=MAX_DEPTH, min_world=MIN_WORLD
)
print(f"Free leaves: {len(free_leaves)} | Blocked leaves: {len(blocked_leaves)}")

# Build edge maps and adjacency for free cells
free_edges = build_edge_map(free_leaves)
free_adj = build_adjacency_from_edges(free_leaves, free_edges)

# Build graph arrays and partition
centers, metis_w, free_adj_lists, free_area_weights = build_graph_arrays(
    free_leaves, free_adj, lat
)
labels = partition_graph(free_adj_lists, metis_w, K_PARTS)
print(f"Partitioned free cells into {K_PARTS} parts")

# Assign blocked-hole components to partitions
blocked_edges = build_edge_map(blocked_leaves)
blocked_labels = assign_holes_to_partitions(
    blocked_leaves,
    blocked_edges,
    free_edges,
    labels,
    free_area_weights,
    K_PARTS,
    lat,
    load_penalty=0.0,
)
print("Assigned blocked holes to partitions")

# Build coverage polygons (hole-free faces) and plot as numpy arrays
print("Building coverage polygons...")
part_polys_np = build_coverage_polygons_np(
    free_leaves, labels, blocked_leaves, blocked_labels, K_PARTS, lat
)

print("Plotting...")

# Plot partitions at cell level
if PLOT_QUADTREE:
    plt.figure(figsize=(8, 8))
    plot_partitions_cells(
        free_leaves, lat, labels, blocked_leaves, blocked_labels, cmap_name="tab20"
    )
    if PLOT_BBOXES:
        plot_bboxes(bboxes)
    if PLOT_FOOTPRINTS:
        plot_footprints(footprints)
    plt.title("Partition (quadtree cells)")
    plt.tight_layout()

# Plot partitions at polygon level
if PLOT_POLYGONS:
    plt.figure(figsize=(8, 8))
    plot_partition_polygons_np(part_polys_np, cmap_name="tab20")
    if PLOT_FOOTPRINTS:
        plot_footprints(footprints)
    plt.title("Partitions (coverage polygons)")
    plt.tight_layout()

if PLOT_QUADTREE or PLOT_POLYGONS:
    plt.show()
