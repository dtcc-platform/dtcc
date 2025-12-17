import math
import numpy as np
import meshio
from pathlib import Path

from shapely import area

OUTDIR = Path("results_CDT")  # adjust to results_new_CDT if needed
VTU_NAMES = [
      "A_unit_square_default.vtu",
      "B_unit_square_with_inner_polygon.vtu",
      "C_city_100.vtu",
      "D_city_100.vtu",
      "D_city_50.vtu",
      "D_city_20.vtu",
      "D_city_10.vtu",
      "D_city_5.vtu",
      "D_city_2.vtu",
      "D_city_1.vtu",
  ]


def triangle_stats(points, tris):
  if not len(tris):
          return None
  pts = points[:, :2]
  idx = tris.astype(np.int64)
  v0 = pts[idx[:, 0]]
  v1 = pts[idx[:, 1]]
  v2 = pts[idx[:, 2]]

  a = np.linalg.norm(v1 - v2, axis=1)
  b = np.linalg.norm(v2 - v0, axis=1)
  c = np.linalg.norm(v0 - v1, axis=1)

  s = 0.5 * (a + b + c)
  area = np.sqrt(np.clip(s * (s - a) * (s - b) * (s - c), 0.0, None))
  valid = area > 0
  if not np.any(valid):
      return None

  a = a[valid]; b = b[valid]; c = c[valid]; area = area[valid]
  cosA = np.clip((b*b + c*c - a*a) / (2*b*c), -1.0, 1.0)
  cosB = np.clip((a*a + c*c - b*b) / (2*a*c), -1.0, 1.0)
  cosC = np.clip((a*a + b*b - c*c) / (2*a*b), -1.0, 1.0)
  angles = np.vstack((np.arccos(cosA), np.arccos(cosB), np.arccos(cosC))) * 180.0 / math.pi 
  min_angles = np.min(angles, axis=0)

  aspect_ratio = np.maximum.reduce([a, b, c]) / np.minimum.reduce([a, b, c])
  return {
          "count": len(area),
          "min_angles": min_angles,
          "aspect_ratio": aspect_ratio,
          "area": area,
      }

def summarize(values):
      return {
          "min": float(np.min(values)),
          "p10": float(np.percentile(values, 10)),
          "median": float(np.percentile(values, 50)),
          "p90": float(np.percentile(values, 90)),
          "max": float(np.max(values)),
          "mean": float(np.mean(values)),
      }



if __name__ == "__main__":
  OUTDIR.mkdir(exist_ok=True)
  lines = []
  for name in VTU_NAMES:
      path = OUTDIR / name
      if not path.exists():
          continue
      mesh = meshio.read(path)
      tri_cells = next((cells.data for cells in mesh.cells if cells.type ==
  "triangle"), None)
      if tri_cells is None:
          continue

      stats = triangle_stats(mesh.points, tri_cells)
      if stats is None:
          continue

      angles_summary = summarize(stats["min_angles"])
      aspect_summary = summarize(stats["aspect_ratio"])
      area_summary = summarize(stats["area"])

      lines.append(f"Case: {name}")
      lines.append(f"  triangles: {stats['count']}")
      lines.append(
          "  min_angle_deg: min={min:.3f} p10={p10:.3f} median={median:.3f} "
          "p90={p90:.3f} max={max:.3f} mean={mean:.3f}".format(**angles_summary)
      )
      lines.append(
          "  aspect_ratio: min={min:.3f} p10={p10:.3f} median={median:.3f} "
          "p90={p90:.3f} max={max:.3f} mean={mean:.3f}".format(**aspect_summary)
      )
      lines.append(
          "  area: min={min:.6f} p10={p10:.6f} median={median:.6f} "
          "p90={p90:.6f} max={max:.6f} mean={mean:.6f}".format(**area_summary)
      )
      lines.append("")

  (OUTDIR / "metrics_CDT.log").write_text("\n".join(lines))
  print("Wrote", OUTDIR / "metrics_CDT.log")