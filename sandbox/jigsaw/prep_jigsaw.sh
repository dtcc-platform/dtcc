#!/usr/bin/env bash
set -euo pipefail

# Get directory of this script (absolute path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Repo to clone
REPO_URL="https://github.com/dengwirda/jigsaw-python.git"
REPO_NAME="jigsaw-python"

# Clone repo into current directory (where script lives)
cd "$SCRIPT_DIR"
if [ -d "$REPO_NAME" ]; then
    echo "Removing existing repo $REPO_NAME..."
    rm -rf "$REPO_NAME"
fi
git clone "$REPO_URL"

# Replace CMakeLists.txt with your own
cp "$SCRIPT_DIR/CMakeLists.txt" "$SCRIPT_DIR/$REPO_NAME/external/jigsaw/src/CMakeLists.txt"

# Enter repo and build
cd "$SCRIPT_DIR/$REPO_NAME"
python build.py

# Install with pip
pip install .
