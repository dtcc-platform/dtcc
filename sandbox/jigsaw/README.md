# DTCC JIGSAW Sandbox

This sandbox wraps the JIGSAW mesher via `jigsawpy` and exposes convenience helpers for polygon meshing.

## Quick Start

Run the prep script once to build and install a working `jigsawpy`:

```bash
cd dtcc/sandbox/jigsaw
bash prep_jigsaw.sh
```

The script will:
- Clone the `jigsaw-python` repository locally. [[Github]](https://github.com/dengwirda/jigsaw-python/tree/master)
- Replace the faulty `external/jigsaw/src/CMakeLists.txt` from the repo with our fixed version in this folder.
- Build the native JIGSAW binaries and Python bindings.
- Install the package via `pip install .`.

The prep script handles cloning, building, and installing; no manual steps are required beyond running it.

After this completes you can run either of the drivers:

```bash
python dtcc/sandbox/jigsaw/test.py
python dtcc/sandbox/jigsaw/bench.py
```

## Core Functions

- Primary meshing function: `meshing.py: mesh_polygon_bound()`
  - Generates the meshes we want (triangular surface mesh with region labeling/interfaces).
  - Key size control: `maxh` (global), with optional edge refinement.

- Edge size field: `meshing.py: _build_edge_hfun_grid()`
  - Controls edge-aware sizing near input boundaries.
  - Parameters: `edge_hmin` (minimum near edges) and `edge_band` (decay distance), blended with `maxh`.

Adjust these parameters in your call to tune mesh resolution globally and near boundaries.



