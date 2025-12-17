#!/usr/bin/env bash
set -euo pipefail

# Directory where the script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Cleaning up jigsaw build environment in $SCRIPT_DIR ..."

# Remove cloned repo if present
if [ -d "$SCRIPT_DIR/jigsaw-python" ]; then
    echo "Removing jigsaw-python repo..."
    rm -rf "$SCRIPT_DIR/jigsaw-python"
fi

# Remove "output" directory if present
if [ -d "$SCRIPT_DIR/output" ]; then
    echo "Removing output directory..."
    rm -rf "$SCRIPT_DIR/output"
fi

# Find and delete all .vtu and .vtk files under this directory tree
echo "Removing .vtu and .vtk files..."
find "$SCRIPT_DIR" -type f \( -name "*.vtu" -o -name "*.vtk" \) -exec rm -f {} +

echo "Cleanup complete."
