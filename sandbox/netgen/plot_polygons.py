from pylab import *


def plot_polygon(polygon, index=None):
    polygon = array(polygon)
    plot(polygon[:, 0], polygon[:, 1], "-o")
    plot(polygon[[0, -1], 0], polygon[[0, -1], 1], "b-o")
    xmean = mean(polygon[:, 0])
    ymean = mean(polygon[:, 1])
    if index is not None:
        text(
            xmean,
            ymean,
            str(index),
            fontsize=12,
            color="red",
            horizontalalignment="center",
            verticalalignment="center",
        )


to_coords = lambda s: [(float(s[i]), float(s[i + 1])) for i in range(0, len(s), 2)]

with open("testcase.txt") as f:
    lines = f.read().split("\n")
    exterior = to_coords(lines[0].split(" "))
    interiors = [to_coords(l.split(" ")) for l in lines[1:-1]]

plot_polygon(exterior)

for i, p in enumerate(interiors):
    plot_polygon(p, i)

show()
