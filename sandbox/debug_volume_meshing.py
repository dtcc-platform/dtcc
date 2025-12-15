"""
Enhanced debug script for volume meshing workflow.

This script helps debug the complete pipeline:
1. Building preprocessing (merge -> simplify)
2. Surface mesh generation (Spade)
3. Volume mesh generation (TetGen)

It adds extensive logging, intermediate output saves, and geometry validation
to help identify where the segfault occurs.

Based on the updated build_city_volume_mesh() function in:
dtcc_core/builder/geometry_builders/meshes.py
"""
from typing import Any, Dict, Optional, List, cast
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from dtcc_core.model import (
    Mesh,
    VolumeMesh,
    Building,
    Terrain,
    City,
    Surface,
    MultiSurface,
    GeometryType,
    PointCloud,
)

_LOD_PRIORITY: dict[GeometryType, int] = {
    GeometryType.LOD0: 0,
    GeometryType.LOD1: 1,
    GeometryType.LOD2: 2,
    GeometryType.LOD3: 3,
}

from dtcc_core.builder.model_conversion import (
    create_builder_polygon,
    create_builder_surface,
    raster_to_builder_gridfield,
)

from dtcc_core.builder import _dtcc_builder

from dtcc_core.builder.building.modify import (
    merge_building_footprints,
    simplify_building_footprints,
    get_footprint,
)

from dtcc_core.builder.meshing.convert import mesh_to_raster

from dtcc.logging import debug, info, warning, error

from dtcc_core.builder.meshing.tetgen import (
    build_volume_mesh as tetgen_build_volume_mesh,
    get_default_tetgen_switches,
    is_tetgen_available,
)

import dtcc


class DebugVolumeMesher:
    """Debug wrapper for volume meshing with extensive logging and validation."""

    def __init__(self, output_dir: str = "debug_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.step = 0

    def log_step(self, message: str):
        """Log a step with numbering."""
        self.step += 1
        info(f"\n{'='*80}")
        info(f"STEP {self.step}: {message}")
        info(f"{'='*80}")

    def save_footprints_plot(self, footprints: List, filename: str, title: str = None):
        """Save building footprints as a plot."""
        try:
            fig, ax = plt.subplots(figsize=(12, 12))

            for i, fp in enumerate(footprints):
                if fp is None:
                    continue
                try:
                    poly = fp.to_polygon() if hasattr(fp, 'to_polygon') else fp

                    # Exterior boundary
                    x, y = poly.exterior.xy
                    ax.plot(x, y, color="blue", linewidth=1.5, label="Exterior" if i == 0 else "")

                    # Holes (interior rings)
                    for interior in poly.interiors:
                        x, y = interior.xy
                        ax.plot(x, y, color="red", linewidth=1, label="Holes" if i == 0 else "")
                except Exception as e:
                    warning(f"Failed to plot footprint {i}: {e}")

            ax.set_aspect("equal")
            ax.set_title(title or filename)
            ax.legend()
            ax.grid(True, alpha=0.3)

            output_path = self.output_dir / f"{filename}.png"
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            info(f"Saved plot: {output_path}")
        except Exception as e:
            error(f"Failed to save plot {filename}: {e}")

    def validate_geometry(self, geom, index: int) -> dict:
        """Validate a single geometry and return stats."""
        stats = {
            "index": index,
            "valid": False,
            "empty": True,
            "area": 0.0,
            "error": None
        }

        try:
            if geom is None:
                stats["error"] = "None geometry"
                return stats

            poly = geom.to_polygon() if hasattr(geom, 'to_polygon') else geom

            stats["empty"] = poly.is_empty if hasattr(poly, 'is_empty') else True
            stats["valid"] = poly.is_valid if hasattr(poly, 'is_valid') else False
            stats["area"] = poly.area if hasattr(poly, 'area') else 0.0

            if not stats["valid"]:
                stats["error"] = f"Invalid geometry: {poly.is_valid}"
            elif stats["empty"]:
                stats["error"] = "Empty geometry"
            elif stats["area"] <= 0:
                stats["error"] = f"Zero/negative area: {stats['area']}"

        except Exception as e:
            stats["error"] = str(e)

        return stats

    def validate_footprints(self, footprints: List, name: str) -> List[int]:
        """Validate all footprints and return valid indices."""
        self.log_step(f"Validating {name}")

        valid_indices = []
        invalid_count = 0

        for i, fp in enumerate(footprints):
            stats = self.validate_geometry(fp, i)

            if stats["error"]:
                warning(f"  Footprint {i}: {stats['error']}")
                invalid_count += 1
            else:
                valid_indices.append(i)

        info(f"  Total footprints: {len(footprints)}")
        info(f"  Valid: {len(valid_indices)}")
        info(f"  Invalid: {invalid_count}")

        return valid_indices

    def build_city_volume_mesh_debug(
        self,
        city: City,
        lod: GeometryType = GeometryType.LOD1,
        domain_height: float = 100.0,
        max_mesh_size: float = 10.0,
        min_mesh_angle: float = 25.0,
        merge_buildings: bool = True,
        min_building_detail: float = 0.5,
        min_building_area: float = 15.0,
        merge_tolerance: float = 0.5,
        smoothing: int = 0,
        boundary_face_markers: bool = True,
        tetgen_switches: Optional[Dict[str, Any]] = None,
        tetgen_switch_overrides: Optional[Dict[str, Any]] = None,
        stop_before_surface_mesh: bool = False,
        stop_before_volume_mesh: bool = False,
    ) -> Optional[VolumeMesh]:
        """
        Debug version of build_city_volume_mesh with extensive logging and checkpoints.

        Additional Parameters
        ---------------------
        stop_before_surface_mesh : bool
            If True, stop execution before calling build_city_surface_mesh (for testing preprocessing)
        stop_before_volume_mesh : bool
            If True, stop after surface mesh but before volume mesh (for testing surface mesh generation)
        """

        # Fallback DTCC volume mesher parameters
        smoother_max_iterations = 5000
        smoothing_relative_tolerance = 0.005
        aspect_ratio_threshold = 10.0
        debug_step = 7

        # =====================================================================
        # 1. VALIDATE INPUT AND TERRAIN
        # =====================================================================
        self.log_step("Validating input and terrain")

        buildings = city.buildings
        if not buildings:
            warning("City has no buildings.")
            return None

        info(f"Initial building count: {len(buildings)}")

        terrain = city.terrain
        if terrain is None:
            raise ValueError("City has no terrain data.")

        terrain_raster = terrain.raster
        terrain_mesh = terrain.mesh
        if terrain_raster is None and terrain_mesh is None:
            raise ValueError("City terrain has no data.")
        if terrain_raster is None and terrain_mesh is not None:
            terrain_raster = mesh_to_raster(terrain_mesh, cell_size=max_mesh_size)

        info(f"Terrain bounds: {terrain.bounds}")
        info(f"Terrain raster shape: {terrain_raster.data.shape if terrain_raster else 'N/A'}")

        # =====================================================================
        # 2. PREPROCESS BUILDINGS
        # =====================================================================
        self.log_step("Preprocessing buildings")

        if merge_buildings:
            info(f"Merging {len(buildings)} buildings...")

            # First merge pass
            info("  Sub-step: First merge pass")
            step1_buildings = cast(
                List[Building],
                merge_building_footprints(
                    buildings,
                    lod=GeometryType.LOD0,
                    max_distance=merge_tolerance,
                    min_area=min_building_area,
                    return_index_map=False,
                ),
            )
            info(f"  After first merge: {len(step1_buildings)} buildings")

            # Second merge pass (merge touching buildings)
            info("  Sub-step: Second merge pass (touching buildings)")
            step2_buildings = cast(
                List[Building],
                merge_building_footprints(
                    step1_buildings,
                    GeometryType.LOD0,
                    max_distance=0.0,
                    min_area=min_building_area,
                    return_index_map=False,
                ),
            )
            info(f"  After second merge: {len(step2_buildings)} buildings")

            # Simplify footprints
            info("  Sub-step: Simplifying footprints")
            simplified_footprints = cast(
                List[Building],
                simplify_building_footprints(
                    step2_buildings,
                    min_building_detail,
                    lod=GeometryType.LOD0,
                    return_index_map=False,
                ),
            )
            info(f"  After simplification: {len(simplified_footprints)} buildings")

            # Extract footprints
            building_footprints = [
                b.get_footprint(GeometryType.LOD0) for b in simplified_footprints
            ]
            processed_buildings = simplified_footprints

            info(f"After merging: {len(building_footprints)} buildings")
        else:
            # No merging - use original buildings
            building_footprints = [b.get_footprint(lod) for b in buildings]
            processed_buildings = buildings

        # Save initial footprints plot
        self.save_footprints_plot(
            building_footprints,
            "01_initial_footprints",
            f"Initial Footprints (n={len(building_footprints)})"
        )

        # =====================================================================
        # 3. VALIDATE AND FILTER FOOTPRINTS
        # =====================================================================
        valid_indices = self.validate_footprints(building_footprints, "building footprints")

        if not valid_indices:
            raise ValueError("No valid building footprints available for meshing.")

        building_footprints = [building_footprints[i] for i in valid_indices]
        processed_buildings = [processed_buildings[i] for i in valid_indices]

        info(f"Using {len(valid_indices)} valid building footprints for meshing")

        # Save validated footprints plot
        self.save_footprints_plot(
            building_footprints,
            "02_validated_footprints",
            f"Validated Footprints (n={len(building_footprints)})"
        )

        # =====================================================================
        # 4. COMPUTE SUBDOMAIN RESOLUTION
        # =====================================================================
        self.log_step("Computing subdomain resolution")

        subdomain_resolution = []
        for i, building in enumerate(processed_buildings):
            try:
                height = building.height
                if height is None or height <= 0:
                    warning(f"  Building {i}: Invalid height {height}, using max_mesh_size")
                    height = max_mesh_size
                resolution = min(height, max_mesh_size)
                subdomain_resolution.append(resolution)
                debug(f"  Building {i}: height={height:.2f}, resolution={resolution:.2f}")
            except (AttributeError, TypeError) as e:
                warning(f"  Building {i}: Failed to get height ({e}), using max_mesh_size")
                subdomain_resolution.append(max_mesh_size)

        info(f"Subdomain resolution computed for {len(subdomain_resolution)} buildings")
        info(f"  Min: {min(subdomain_resolution):.2f}")
        info(f"  Max: {max(subdomain_resolution):.2f}")
        info(f"  Mean: {np.mean(subdomain_resolution):.2f}")

        # =====================================================================
        # 5. PREPARE BUILDER OBJECTS
        # =====================================================================
        self.log_step("Preparing builder objects")

        _surfaces = [create_builder_surface(footprint) for footprint in building_footprints]
        hole_surfaces: list = []
        lod_switch_value = _LOD_PRIORITY.get(lod, _LOD_PRIORITY[GeometryType.LOD3])
        meshing_directives = [lod_switch_value] * len(_surfaces)
        _dem = raster_to_builder_gridfield(terrain_raster)

        info(f"Created {len(_surfaces)} builder surfaces")
        info(f"Meshing directives: all set to {lod_switch_value} (LOD={lod})")

        # =====================================================================
        # CHECKPOINT: Stop before surface mesh if requested
        # =====================================================================
        if stop_before_surface_mesh:
            warning("CHECKPOINT: Stopping before surface mesh generation")
            return None

        # =====================================================================
        # 6. BUILD VOLUME MESH - TETGEN PATH
        # =====================================================================
        if is_tetgen_available():
            self.log_step("Building volume mesh with TetGen")

            # Validate inputs
            info(f"Number of surfaces: {len(_surfaces)}")
            info(f"Number of subdomain resolutions: {len(subdomain_resolution)}")
            info(f"Subdomain resolutions: {subdomain_resolution}")
            info(f"Max mesh size: {max_mesh_size}, Min angle: {min_mesh_angle}, Smoothing: {smoothing}")

            if len(_surfaces) != len(subdomain_resolution):
                raise ValueError(
                    f"Mismatch: {len(_surfaces)} surfaces but {len(subdomain_resolution)} resolution values"
                )

            # Build surface mesh
            info("Calling build_city_surface_mesh...")
            merge_meshes = True
            sort_triangles = False

            try:
                builder_mesh = _dtcc_builder.build_city_surface_mesh(
                    _surfaces,
                    hole_surfaces,
                    meshing_directives,
                    subdomain_resolution,
                    _dem,
                    max_mesh_size,
                    min_mesh_angle,
                    smoothing,
                    merge_meshes,
                    sort_triangles,
                )
                info("✓ Surface mesh generation succeeded!")
            except Exception as e:
                error(f"✗ Surface mesh generation FAILED: {e}")
                raise

            surface_mesh = builder_mesh[0].from_cpp()

            # Save surface mesh
            surface_mesh_path = self.output_dir / "03_surface_mesh.vtk"
            surface_mesh.save(str(surface_mesh_path))
            info(f"Saved surface mesh: {surface_mesh_path}")

            # Validate surface mesh
            self.log_step("Validating surface mesh")
            if surface_mesh.faces is None or len(surface_mesh.faces) == 0:
                raise ValueError("Surface mesh has no faces.")
            if surface_mesh.markers is None or len(surface_mesh.markers) == 0:
                raise ValueError("Surface mesh has no face markers.")

            info(f"Surface mesh stats:")
            info(f"  Vertices: {len(surface_mesh.vertices)}")
            info(f"  Faces: {len(surface_mesh.faces)}")
            info(f"  Markers: {len(surface_mesh.markers)} unique values: {np.unique(surface_mesh.markers)}")

            # =====================================================================
            # CHECKPOINT: Stop before volume mesh if requested
            # =====================================================================
            if stop_before_volume_mesh:
                warning("CHECKPOINT: Stopping before volume mesh generation")
                return None

            # Configure TetGen switches
            self.log_step("Configuring TetGen and building volume mesh")
            switches_params = get_default_tetgen_switches()
            if tetgen_switches:
                switches_params.update(tetgen_switches)

            info(f"TetGen switches: {switches_params}")

            # Build volume mesh with TetGen
            try:
                info("Calling TetGen...")
                volume_mesh = tetgen_build_volume_mesh(
                    mesh=surface_mesh,
                    build_top_sidewalls=True,
                    top_height=domain_height,
                    switches_params=switches_params,
                    switches_overrides=tetgen_switch_overrides,
                    return_boundary_faces=boundary_face_markers,
                )
                info("✓ Volume mesh generation succeeded!")
            except Exception as e:
                error(f"✗ Volume mesh generation FAILED: {e}")
                raise

            # Save volume mesh
            if isinstance(volume_mesh, tuple):
                vm, _ = volume_mesh
            else:
                vm = volume_mesh

            volume_mesh_path = self.output_dir / "04_volume_mesh.vtk"
            vm.save(str(volume_mesh_path))
            info(f"Saved volume mesh: {volume_mesh_path}")

            self.log_step("COMPLETE - Volume mesh generated successfully!")
            return vm

        # =====================================================================
        # 7. BUILD VOLUME MESH - FALLBACK DTCC PATH
        # =====================================================================
        else:
            self.log_step("Building volume mesh with fallback DTCC mesher")
            warning("TetGen not available, using fallback mesher")

            # Convert footprints to builder polygons for ground mesh
            _building_polygons = [
                create_builder_polygon(footprint.to_polygon())
                for footprint in building_footprints
            ]

            # Build ground mesh
            _ground_mesh = _dtcc_builder.build_ground_mesh(
                _building_polygons,
                [],
                subdomain_resolution,
                terrain.bounds.xmin,
                terrain.bounds.ymin,
                terrain.bounds.xmax,
                terrain.bounds.ymax,
                max_mesh_size,
                min_mesh_angle,
                True,
            )

            # Create volume mesh builder
            volume_mesh_builder = _dtcc_builder.VolumeMeshBuilder(
                _surfaces, _dem, _ground_mesh, domain_height
            )

            # Build volume mesh
            _volume_mesh = volume_mesh_builder.build(
                smoother_max_iterations,
                smoothing_relative_tolerance,
                0.0,
                aspect_ratio_threshold,
                debug_step,
            )
            volume_mesh = _volume_mesh.from_cpp()

            # Add boundary face markers if requested
            if boundary_face_markers:
                computed_markers = _dtcc_builder.compute_boundary_face_markers(_volume_mesh)
                if computed_markers is not None:
                    volume_mesh.boundary_markers = computed_markers

            volume_mesh_path = self.output_dir / "04_volume_mesh_fallback.vtk"
            volume_mesh.save(str(volume_mesh_path))
            info(f"Saved volume mesh: {volume_mesh_path}")

            return volume_mesh


# =============================================================================
# MAIN DEBUG SCRIPT
# =============================================================================
if __name__ == "__main__":
    # Create debug mesher
    debugger = DebugVolumeMesher(output_dir="debug_output")

    # Define bounds (use your problematic area)
    h = 500.0
    bounds = dtcc.Bounds(319391, 6399290, 319391 + h, 6399290 + h)

    # Example problematic area #2
    h = 200
    bounds = dtcc.Bounds(319882, 6399450, 320173 +h, 6399740 +h)

    info(f"Testing area with bounds: {bounds}")

    # Download data
    info("Downloading pointcloud and building footprints...")
    pointcloud = dtcc.download_pointcloud(bounds=bounds)
    buildings = dtcc.download_footprints(bounds=bounds)

    # Remove global outliers
    pointcloud = pointcloud.remove_global_outliers(3.0)

    # Build terrain raster
    raster = dtcc.build_terrain_raster(
        pointcloud, cell_size=2, radius=3, ground_only=True
    )

    # Extract roof points and compute building heights
    buildings = dtcc.extract_roof_points(buildings, pointcloud)
    buildings = dtcc.compute_building_heights(buildings, raster, overwrite=True)

    # Create city
    city = dtcc.City()
    city.add_terrain(raster)
    city.add_buildings(buildings, remove_outside_terrain=True)

    # Configure meshing parameters
    domain_height = 80.0
    max_mesh_size = 10.0

    tetgen_switches = {
        "plc": True,
        "max_volume": max_mesh_size,
        "quality": None,
        "extra": "-VVV",  # Very verbose for debugging
    }

    # OPTION 1: Test preprocessing only
    # Uncomment to test just the preprocessing step
    # debugger.build_city_volume_mesh_debug(
    #     city,
    #     merge_buildings=True,
    #     domain_height=domain_height,
    #     max_mesh_size=max_mesh_size,
    #     tetgen_switches=tetgen_switches,
    #     boundary_face_markers=False,
    #     stop_before_surface_mesh=True,  # Stop before the crash
    # )

    # OPTION 2: Test up to surface mesh
    # Uncomment to test preprocessing + surface mesh generation
    # debugger.build_city_volume_mesh_debug(
    #     city,
    #     merge_buildings=True,
    #     domain_height=domain_height,
    #     max_mesh_size=max_mesh_size,
    #     tetgen_switches=tetgen_switches,
    #     boundary_face_markers=False,
    #     stop_before_volume_mesh=True,  # Stop after surface mesh
    # )

    # OPTION 3: Full run
    try:
        volume_mesh = debugger.build_city_volume_mesh_debug(
            city,
            merge_buildings=True,
            domain_height=domain_height,
            max_mesh_size=max_mesh_size,
            tetgen_switches=tetgen_switches,
            boundary_face_markers=False,
        )
        if volume_mesh:
            info("SUCCESS: Volume mesh created successfully!")
    except Exception as e:
        error(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
