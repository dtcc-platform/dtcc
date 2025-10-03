from dtcc import Bounds, City, Object, GeometryType
from pathlib import Path


from time import time

# Define bounds (a residential area in Helsingborg)
city = City()
h = 1000.0
bounds = Bounds(319891, 6399790, 319891 + h, 6399790 + h, 0, 200)
city.bounds = bounds

# Download pointcloud and building footprints
city.download_pointcloud(filter_on_z_bounds=True)
city.download_footprints()

city.building_heights_from_pointcloud()

surface_mesh = city.build_surface_mesh()

# move to (0,0,0)
surface_mesh.offset_to_origin()
surface_mesh.offset([0, 0, 1])  # lift 1m above ground since we extrude to 0 by default

start = time()
tiles = surface_mesh.tile(tile_size=250, progress=True)
print(f"Tiling took {time()-start:.2f} seconds for {len(tiles)} tiles")

print_tiles = [t.create_printable_solid() for t in tiles]

outdir = Path("tiled_city_meshes")
outdir.mkdir(exist_ok=True, parents=True)

for i, t in enumerate(print_tiles):
    t.save(outdir / f"tiled_city_{i}.stl")
