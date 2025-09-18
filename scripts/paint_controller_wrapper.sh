#!/bin/bash

# Wrapper script to run paint_controller_cpp with correct library paths
# This avoids conflicts with snap-installed libraries

# Set library path to prioritize system libraries
export LD_LIBRARY_PATH="/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Remove any snap library paths that might interfere
export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v '/snap/' | tr '\n' ':' | sed 's/:$//')

# Run the actual executable
exec "$(dirname "$0")/paint_controller_cpp" "$@"
