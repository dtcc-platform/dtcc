#!/usr/bin/env python3


from __future__ import annotations

from pathlib import Path
import numpy as np
import os
import csv

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

from quality_report import triangle_stats, summarize

def read_loops_from_file_and_mesh(
    path: str = "testcase.txt", maxh: float = 5.0, fname: Path | str = "gbg_bound.vtu"
) -> dict:
    outer, loops = read_loops_from_file(path)
    jmesh, pts, tris, regions, lines, dt = mesh_polygon_bound(
        outer, inner_loops=loops, maxh=maxh, return_numpy=True
    )
    # jig.savevtk("jig_gbg_bound.vtk", jmesh)
    print(f'Points: {len(pts)} Triangles: {len(tris)} Regions: {len(set(regions))}')
    tris_per_sec = len(tris) / dt if dt > 0 else 0
    pts_per_sec = len(pts) / dt if dt > 0 else 0
    print(f"Meshing time: {dt:.2f} sec ({tris_per_sec:.1f} tris/sec, {pts_per_sec:.1f} pts/sec)")
    
    tri_stats = triangle_stats(pts, tris)
    if tri_stats is not None:
        print(f"  Triangles: {tri_stats['count']}")
        print(f"  Area: {summarize(tri_stats['area'])}")
        print(f"  Min angles: {summarize(tri_stats['min_angles'])}")
        print(f"  Aspect ratio: {summarize(tri_stats['aspect_ratio'])}")
    else:
        print("  No valid triangles found!")
    
    save_vtu_with_regions_and_lines(pts, tris, regions, lines, fname)
    # Prepare metrics for CSV
    if tri_stats is not None:
        min_area = float(np.min(tri_stats["area"]))
        max_area = float(np.max(tri_stats["area"]))
        max_aspect_ratio = float(np.max(tri_stats["aspect_ratio"]))
        min_angle = float(np.min(tri_stats["min_angles"]))
    else:
        min_area = ""
        max_area = ""
        max_aspect_ratio = ""
        min_angle = ""

    metrics = {
        "max_mesh_size": float(maxh),
        "num_triangles": int(len(tris)),
        "num_points": int(len(pts)),
        "time": float(dt),
        "tris_per_sec": float(tris_per_sec),
        "pts_per_sec": float(pts_per_sec),
        "min_area": min_area,
        "max_area": max_area,
        "max_aspect_ratio": max_aspect_ratio,
        "min_angle": min_angle,
    }
    return metrics


if __name__== "__main__":
    print("Benchmarking jigsaw meshing on multiple mesh sizes..")

    testcase_file = Path(__file__).parent.parent / "netgen/testcase.txt"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    csv_path = output_dir / "benchmarks.csv"

    max_mesh_sizes = [100.0, 50.0, 20.0, 10.0, 5.0, 2.0, 1.0, 0.5]
    # Write CSV header
    with open(csv_path, mode="w", newline="") as fcsv:
        writer = csv.DictWriter(
            fcsv,
            fieldnames=[
                "max_mesh_size",
                "num_triangles",
                "num_points",
                "time",
                "tris_per_sec",
                "pts_per_sec",
                "min_area",
                "max_area",
                "max_aspect_ratio",
                "min_angle",
            ],
        )
        writer.writeheader()

        for i, maxh in enumerate(max_mesh_sizes):
            print(f"\nMeshing with maxh={maxh} | Run {i+1} of {len(max_mesh_sizes)}")
            output_file = output_dir / f"gbg_bound_h{maxh}.vtu"
            metrics = read_loops_from_file_and_mesh(
                path=str(testcase_file), maxh=maxh, fname=str(output_file)
            )
            writer.writerow(metrics)
    print(f"Wrote CSV: {csv_path}")
