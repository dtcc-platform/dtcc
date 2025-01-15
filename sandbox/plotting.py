# Simple plotting for DTCC (should be replaced by DTCC Viewer)

import matplotlib.pyplot as plt

COLOR1 = "#F26C2E"
COLOR2 = "#16579A"


def plot_mesh(mesh, show_labels=False, bounds=None):
    fig, ax = plt.subplots()
    for face_index, face in enumerate(mesh.faces):

        # Check if face is within bounds
        x = [mesh.vertices[face[i]][0] for i in range(3)]
        y = [mesh.vertices[face[i]][1] for i in range(3)]
        if bounds is not None:
            if min(x) < bounds.xmin or max(x) > bounds.xmax:
                continue
            if min(y) < bounds.ymin or max(y) > bounds.ymax:
                continue

        # Plot face
        _x = x + [x[0]]
        _y = y + [y[0]]
        marker = mesh.markers[face_index]
        if marker >= 0:
            ax.fill(_x, _y, color=COLOR2)
        elif marker == -1:
            ax.fill(_x, _y, color=COLOR2, alpha=0.5)
        ax.plot(_x, _y, color=COLOR1, linewidth=0.5)

        # Plot face index
        color = COLOR2 if marker <= -2 else "white"
        if show_labels:
            xc = sum(x) / 3
            yc = sum(y) / 3
            ax.text(
                xc,
                yc,
                str(face_index),
                color=color,
                ha="center",
                va="center",
                fontsize=5,
            )

    ax.set_aspect("equal")
    plt.show()
