# Experimenting with how to represent quantities

from dtcc import *
import numpy as np


def grid_scalar_0(grid):
    b = grid.bounds
    c = grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    f = -np.sin(y) + 0.1 * (x**2 - 2 * x * y)
    return f
    # return f.reshape(-1, 1)


def grid_scalar_1(grid):
    b = grid.bounds
    c = grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    f = np.sin(2 * np.pi * x) * np.sin(2 * np.pi * y)
    return f
    # return f.reshape(-1, 1)


def grid_vector_0(grid):
    b = grid.bounds
    c = grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    ux = -np.sin(y) + 0.1 * (x**2 - 2 * x * y)
    uy = np.sin(x) + 0.1 * (y**2 - 2 * x * y)
    return np.column_stack([ux, uy])


def grid_vector_1(grid):
    b = grid.bounds
    c = grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    ux = np.sin(2 * np.pi * x) * np.sin(2 * np.pi * y)
    uy = np.sin(3 * np.pi * x) * np.sin(3 * np.pi * y)
    return np.column_stack([ux, uy])


def volume_grid_scalar_0(grid):
    b = grid.bounds
    c = grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    z = (c[:, 2] - b.ymin) / b.depth
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    z = z * 8 - 4  # Rescale to [-4, 4]
    f = -np.sin(y) + 0.1 * (x**2 - 2 * x * y) + z
    return f
    # return f.reshape(-1, 1)


def volume_grid_scalar_1(grid):
    b = grid.bounds
    c = grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    z = (c[:, 2] - b.ymin) / b.depth
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    z = z * 8 - 4  # Rescale to [-4, 4]
    f = np.sin(2 * np.pi * x) * np.sin(2 * np.pi * y) * np.sin(2 * np.pi * z)
    return f
    # return f.reshape(-1, 1)


def volume_grid_vector_0(grid):
    b = grid.bounds
    c = grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    ux = -np.sin(y) + 0.1 * (x**2 - 2 * x * y)
    uy = np.sin(x) + 0.1 * (y**2 - 2 * x * y)
    uz = x - y
    return np.column_stack([ux, uy, uz])


def volume_grid_vector_1(grid):
    b = grid.bounds
    c = grid.coordinates()
    x = (c[:, 0] - b.xmin) / b.width
    y = (c[:, 1] - b.ymin) / b.height
    x = x * 8 - 4  # Rescale to [-4, 4]
    y = y * 8 - 4  # Rescale to [-4, 4]
    ux = np.sin(2 * np.pi * x) * np.sin(2 * np.pi * y) * np.sin(2 * np.pi * x)
    uy = np.sin(3 * np.pi * x) * np.sin(3 * np.pi * y) * np.sin(3 * np.pi * x)
    uz = np.sin(4 * np.pi * x) * np.sin(4 * np.pi * y) * np.sin(4 * np.pi * x)
    return np.column_stack([ux, uy, uz])


# Load a city model
city = load_cityjson("DenHaag_01.city.json")  # FIXME: Should work with load_city()

# Add some geometries to the city
bounds = city.bounds
bounds.zmax = 100
n = 3
grid = Grid(bounds=bounds, width=n, height=n)
volume_grid = VolumeGrid(bounds=bounds, width=n, height=n, depth=n)
city.add_geometry(grid, "grid")
city.add_geometry(volume_grid, "volume_grid")

# Create some fields
f0 = Field(
    name="T",
    unit="C",
    description="Temperature",
    values=grid_scalar_0(grid),
    dim=1,
)
f1 = Field(
    name="p",
    unit="Pa",
    description="Pressure",
    values=grid_scalar_1(grid),
    dim=1,
)
F0 = Field(
    name="U",
    unit="m/s",
    description="Velocity",
    values=grid_vector_0(grid),
    dim=2,
)
F1 = Field(
    name="B",
    unit="T",
    description="Magnetic field",
    values=grid_vector_1(grid),
    dim=2,
)
g0 = Field(
    name="T",
    unit="C",
    description="Temperature",
    values=volume_grid_scalar_0(volume_grid),
    dim=1,
)
g1 = Field(
    name="p",
    unit="Pa",
    description="Pressure",
    values=volume_grid_scalar_1(volume_grid),
    dim=1,
)
G0 = Field(
    name="U",
    unit="m/s",
    description="Velocity",
    values=volume_grid_vector_0(volume_grid),
    dim=3,
)
G1 = Field(
    name="B",
    unit="T",
    description="Magnetic field",
    values=volume_grid_vector_1(volume_grid),
    dim=3,
)

# Add fields
city.add_field(f0, "grid")
city.add_field(f1, "grid")
city.add_field(F0, "grid")
city.add_field(F1, "grid")
city.add_field(g0, "volume_grid")
city.add_field(g1, "volume_grid")
city.add_field(G0, "volume_grid")
city.add_field(G1, "volume_grid")

# FIXME: Writing protobuf currently fails since City has a geometry that is not a Geometry
for key, val in city.geometry.items():
    print(key, type(val))

# Save the city model
city.save("city_with_fields.pb")
_city = load_city("city_with_fields.pb")


# View the quantities (how should this be done?)
