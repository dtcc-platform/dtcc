#!/usr/bin/env python3

"""
Test routines for polygon meshing with JIGSAW.

Usage: 
From the dtcc-agentic-meshing repo root, run:
python -m jigsaw.test
"""


from __future__ import annotations
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import numpy as np

from meshing import (
    mesh_polygon,
    mesh_polygon_with_interfaces,
    mesh_polygon_fill,
    mesh_polygon_bound,
)

from utils import (
    save_vtu,
    save_vtu_with_regions_and_lines,
    read_loops_from_file,
)

import jigsawpy as jig
from jigsawpy import jigsaw_def_t


TESTCASE_FILE = Path(__file__).parent.parent/ "netgen/testcase.txt"



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
    path: str = "testcase.txt", maxh: float = 5.0, fname: str = "gbg_removeholes.vtu"
) -> None:
    outer, loops = read_loops_from_file(path)
    _, pts, tris, eds = mesh_polygon(
        outer, inner_loops=loops, maxh=maxh, return_numpy=True
    )
    save_vtu(pts, tris, eds, fname)

def read_loops_from_file_and_mesh_interfaces(
    path: str = "testcase.txt", maxh: float = 5.0, fname: str = "gbg_interfaces.vtu"
) -> None:
    outer, loops = read_loops_from_file(path)
    jmesh, pts, tris, regions, lines, dt = mesh_polygon_with_interfaces(
        outer, inner_loops=loops, maxh=maxh, return_numpy=True
    )
    jig.savevtk("jig_gbg_interfaces.vtk", jmesh)
    # save_vtu_with_regions_and_lines(pts, tris, regions, lines, fname)

def read_loops_from_file_and_mesh_fill(
    path: str = "testcase.txt", maxh: float = 5.0, fname: str = "gbg_filled.vtu"
) -> None:
    outer, loops = read_loops_from_file(path)
    jmesh, pts, tris, regions, lines, dt = mesh_polygon_fill(
        outer, inner_loops=loops, maxh=maxh, return_numpy=True
    )
    # save_vtu_with_regions_and_lines(pts, tris, regions, lines, fname)
    jig.savevtk("jig_gbg_filled.vtk", jmesh)

def read_loops_from_file_and_mesh_bound(
    path: str = "testcase.txt", maxh: float = 5.0, fname: str = "gbg_bound.vtu"
) -> None:
    outer, loops = read_loops_from_file(path)
    jmesh, pts, tris, regions, lines, dt = mesh_polygon_bound(
        outer, inner_loops=loops, maxh=maxh, return_numpy=True
    )
    # jig.savevtk("jig_gbg_bound.vtk", jmesh)
    print(f'Points: {len(pts)} Triangles: {len(tris)} Regions: {len(set(regions))}')
    save_vtu_with_regions_and_lines(pts, tris, regions, lines, fname)

if __name__ == "__main__":
    print("Generating test meshes...")

    test_square()
    test_square_with_hole_interfaces()
    test_concave()
    test_L_shape()

    read_loops_from_file_and_mesh_remove_holes(path=str(TESTCASE_FILE), maxh=10.0)
    read_loops_from_file_and_mesh_interfaces(path=str(TESTCASE_FILE), maxh=5.0)
    read_loops_from_file_and_mesh_fill(path=str(TESTCASE_FILE), maxh=5.0)
    read_loops_from_file_and_mesh_bound(path=str(TESTCASE_FILE), maxh=5.0)
    print(
        "Done. Open the .vtu files in ParaView (color by 'region' for *interfaces* cases)."
    )
