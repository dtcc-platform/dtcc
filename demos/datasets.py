# This demo illustrates how to work with DTCC datasets.

from dtcc import datasets, Bounds

# Define bounds (a residential area in Helsingborg)
h = 2000.0
bounds = Bounds(319891, 6399790, 319891 + h, 6399790 + h)

datasets.pointcloud(bounds=bounds)
