# Experimenting with how to represent quantities

from dtcc import *
import numpy as np


def temperature_values(grid):
    b = grid.bounds
    c = grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    T = -np.sin(y) + 0.1 * (x**2 - 2 * x * y)
    return T.reshape(-1, 1)


def velocity_values(volume_grid):
    b = volume_grid.bounds
    c = volume_grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    z = (c[:, 2] - b.zmin) / b.depth
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    z = z * 8 - 4  # Rescale to [-4, 4]
    ux = -np.sin(y) + 0.1 * (x**2 - 2 * x * y)
    uy = np.sin(x) + 0.1 * (y**2 - 2 * x * y)
    uz = x - y
    return np.column_stack([ux, uy, uz])


# Load a city model
city = load_cityjson("DenHaag_01.city.json")  # FIXME: Should work with load_city()

# Add some geometries to the city
bounds = city.bounds
bounds.zmax = 100
n = 16
grid = Grid(bounds=bounds, width=n, height=n)
volume_grid = VolumeGrid(bounds=bounds, width=n, height=n, depth=n)
city.add_geometry(grid, "grid")
city.add_geometry(volume_grid, "volume_grid")


# Add some quantities to the city
t = temperature_values(grid)
u = velocity_values(volume_grid)
T = Quantity(
    name="T",
    unit="C",
    description="Temperature",
    geometry="grid",
    values=t,
    dim=1,
)
U = Quantity(
    name="U",
    unit="m/s",
    description="Velocity",
    geometry="volume_grid",
    values=u,
    dim=3,
)
city.add_quantity(T)
city.add_quantity(U)

# Save the city model
# city.save("city_with_quantities.pb")

# View the quantities (how should this be done?)
