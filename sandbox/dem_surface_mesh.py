# This script processes a GeoTIFF DEM to create a surface mesh of terrain and building footprints.
# It includes functions for reprojecting rasters, cleaning point clouds, assigning building heights,
# and visualizing building footprints.

# This code needs the `dev/wrapper-spade` branch of dtcc-core with the latest changes (21/10/25).
# The `set_building_heights_from_attribute` function has been checked out from develop branch for this purpose.

# Some awkward processing for the dem is done due to dtcc-data only working with EPSG:3006 in Sweden currently.


from pathlib import Path
from typing import List, Tuple
import numpy as np
import dtcc
from rasterio.crs import CRS
from rasterio.warp import Resampling, calculate_default_transform, reproject
from shapely.geometry import box

from dtcc_core.builder.geometry_builders.buildings import set_building_heights_from_attribute
# from dtcc_core.builder.geometry_builders.buildings import set_building_heights_from_attribute

TARGET_CRS = "EPSG:3006"
DATA_FOLDER = Path("path/to/your/geotiff/folder")  # Update this path accordingly


from typing import List
import matplotlib.pyplot as plt

def plot_building_footprints(buildings: List, n: int = 16):
    """
    Plot the footprints of the first `n` buildings.
    
    Parameters
    ----------
    buildings : List[Building]
        List of building objects with method `.get_footprint().vertices`.
    n : int, optional
        Number of buildings to plot (default = 16).
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    for i, b in enumerate(buildings[:n]):
        verts = b.get_footprint().vertices
        # Expect verts shape (N,2) or (N,3)
        x, y = verts[:, 0], verts[:, 1]

        # close the ring if needed
        if (x[0], y[0]) != (x[-1], y[-1]):
            x = list(x) + [x[0]]
            y = list(y) + [y[0]]

        ax.plot(x, y, '-o', markersize=3, label=f'B{i}')

    ax.set_aspect("equal", adjustable="box")
    ax.set_title(f"First {n} building footprints")
    ax.legend(loc="upper right", fontsize="x-small", ncol=2)
    plt.show()

def assign_random_height(building: dtcc.Building, default_height: float = 10.0) -> float:
    """Assign a random but realistic height based on footprint area."""
    area = 0.0
    footprint = building.lod0
    if footprint is not None:
        if hasattr(footprint, "to_polygon"):
            polygon = footprint.to_polygon(simplify=0.0)
            if polygon is not None and not polygon.is_empty:
                area = polygon.area
        if area == 0.0 and hasattr(footprint, "surfaces"):
            for surface in footprint.surfaces:
                if hasattr(surface, "to_polygon"):
                    poly = surface.to_polygon(simplify=0.0)
                    if poly is not None and not poly.is_empty:
                        area += poly.area
    if area <= 0.0:
        bounds = building.bounds
        if bounds is not None:
            area = bounds.area
    if area <= 0.0:
        area = 1.0
    scale = np.log1p(area / 150.0)
    mean = default_height * (1.0 + 0.3 * scale)
    stddev = max(1.0, mean * 0.15)
    height = float(np.random.normal(mean, stddev))
    if height < 4.0:
        height = 4.0
    building.attributes["height"] = height
    return height

def _sanitize_nodata(value):
    if value is None:
        return None
    if isinstance(value, (int, float, np.integer, np.floating)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def reproject_raster(raster, dst_crs=TARGET_CRS, resampling=Resampling.bilinear):
    """Reproject a DTCC Raster in-place to the requested CRS."""
    src_crs = raster.crs
    if not src_crs:
        raise ValueError("Cannot reproject raster without a source CRS.")
    src_crs_obj = CRS.from_user_input(src_crs)
    dst_crs_obj = CRS.from_user_input(dst_crs)
    if src_crs_obj == dst_crs_obj:
        raster.crs = dst_crs_obj.to_string()
        return raster

    bounds = raster.bounds
    transform = raster.georef
    resolution = None
    if transform.a and transform.e:
        resolution = (abs(transform.a), abs(transform.e))

    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_crs_obj,
        dst_crs_obj,
        raster.width,
        raster.height,
        left=bounds.xmin,
        bottom=bounds.ymin,
        right=bounds.xmax,
        top=bounds.ymax,
        resolution=resolution,
    )

    src_array = raster.data
    src_nodata = _sanitize_nodata(raster.nodata)

    channels = raster.channels
    if channels > 1:
        src_array = np.moveaxis(src_array, -1, 0)
        dst_array = np.empty(
            (channels, dst_height, dst_width), dtype=src_array.dtype
        )
    else:
        dst_array = np.empty((dst_height, dst_width), dtype=src_array.dtype)

    if np.issubdtype(dst_array.dtype, np.floating):
        dst_array.fill(np.nan)
    elif src_nodata is not None:
        dst_array.fill(src_nodata)
    else:
        dst_array.fill(0)

    reproject(
        source=src_array,
        destination=dst_array,
        src_transform=transform,
        src_crs=src_crs_obj,
        src_nodata=src_nodata,
        dst_transform=dst_transform,
        dst_crs=dst_crs_obj,
        dst_nodata=src_nodata,
        resampling=resampling,
    )

    if channels > 1:
        raster.data = np.moveaxis(dst_array, 0, -1)
    else:
        raster.data = dst_array
    raster.georef = dst_transform
    raster.crs = dst_crs_obj.to_string()
    return raster


def drop_invalid_points(pointcloud):
    """Remove NaN/inf coordinates from point cloud to keep downstream builders stable."""
    if len(pointcloud.points) == 0:
        return pointcloud
    mask = np.all(np.isfinite(pointcloud.points), axis=1)
    if np.all(mask):
        return pointcloud
    pointcloud.points = pointcloud.points[mask]
    if len(pointcloud.classification) == len(mask):
        pointcloud.classification = pointcloud.classification[mask]
    if len(pointcloud.intensity) == len(mask):
        pointcloud.intensity = pointcloud.intensity[mask]
    if len(pointcloud.return_number) == len(mask):
        pointcloud.return_number = pointcloud.return_number[mask]
    if len(pointcloud.num_returns) == len(mask):
        pointcloud.num_returns = pointcloud.num_returns[mask]
    pointcloud.calculate_bounds()
    return pointcloud



def main():
    tif_files = sorted(p for p in DATA_FOLDER.iterdir() if p.suffix.lower() == ".tif")
    if not tif_files:
        raise FileNotFoundError(f"No GeoTIFF files found in {DATA_FOLDER}")

    raster = dtcc.io.raster.load(tif_files)
    print("Loaded raster:", raster, raster.crs)
    print("Raster range:", float(np.nanmin(raster.data)), float(np.nanmax(raster.data)))

    raster = reproject_raster(raster, TARGET_CRS)
    print("Reprojected raster CRS:", raster.crs)
    print(
        "Reprojected raster range:",
        float(np.nanmin(raster.data)),
        float(np.nanmax(raster.data)),
    )

    pointcloud = raster.to_pointcloud()
    pointcloud.transform.srs = TARGET_CRS
    pointcloud = drop_invalid_points(pointcloud)
    pointcloud.calculate_bounds()
    z_min = float(np.nanmin(pointcloud.points[:, 2])) if len(pointcloud) else float("nan")
    z_max = float(np.nanmax(pointcloud.points[:, 2])) if len(pointcloud) else float("nan")
    print("Pointcloud Z range:", float(z_min), float(z_max))

    terrain_raster = dtcc.build_terrain_raster(pointcloud, cell_size=10)
    terrain_raster.crs = TARGET_CRS
    terrain_bounds = terrain_raster.bounds
    terrain_min = float(np.nanmin(terrain_raster.data))
    terrain_max = float(np.nanmax(terrain_raster.data))
    print("Terrain raster bounds:", terrain_bounds)
    print("Terrain raster range:", terrain_min, terrain_max)

    # Ready for downstream building footprint queries in EPSG:3006
    print("Request bounds (EPSG:3006):", terrain_bounds)
    # Example:
    buildings = dtcc.download_footprints(bounds=terrain_bounds, provider="OSM", epsg="3006")
    # buildings = buildings[0:50]
    print(f"Downloaded {len(buildings)} building footprints.")
    
    for i, building in enumerate(buildings):
        assign_random_height(building)
        # print(f'Building {i} with height: {building.attributes["height"]}')
    
    buildings  = set_building_heights_from_attribute(buildings,terrain=terrain_raster, height_attribute="height", default_building_height=10.0)
    buildings.reverse()

    city = dtcc.City()
    city.add_terrain(terrain_raster)
    city.add_buildings(buildings, remove_outside_terrain=True)

    # Build surface mesh
    mesh = dtcc.build_city_mesh(city, 
                                lod=dtcc.GeometryType.LOD0,
                                min_building_area = 5.0,
                                smoothing = 2,
                                merge_buildings = True,
                                merge_tolerance = 1.0)

    # Save mesh to file
    mesh.save("dem_only_surface_mesh.obj")
    mesh.save("dem_only_surface_mesh.vtu")

if __name__ == "__main__":
    main()
