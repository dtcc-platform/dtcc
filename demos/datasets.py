# This demo illustrates how to work with DTCC datasets.

from dtcc import datasets, Bounds

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = Bounds(319891, 6399790, 319891 + h, 6399790 + h)

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
