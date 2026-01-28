# This demo illustrates how to work with DTCC datasets.

from dtcc import datasets, Bounds

# Define bounds (central Gothenburg)
x0 = 319995.962899
y0 = 6399009.716755
L = 400.0
bounds = Bounds(x0 - L / 2, y0 - L / 2, x0 + L / 2, y0 + L / 2)

# Print information about all available datasets
datasets.info()

# Get point cloud dataset
pointcloud = datasets.pointcloud(bounds=bounds)
print(pointcloud)
pointcloud.view()

# Get terrain dataset
terrain = datasets.terrain(bounds=bounds)
print(terrain)
terrain.view()

# Get buildings dataset (and view the first building)
buildings = datasets.buildings(bounds=bounds)
print(buildings[0])
buildings[0].view()

# Get volume mesh dataset
volume_mesh = datasets.volumemesh(bounds=bounds)
print(volume_mesh)
volume_mesh.view()
