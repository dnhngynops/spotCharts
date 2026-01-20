#!/bin/bash
# Wrapper script to run Python with WeasyPrint library path set
# Usage: ./run_with_libs.sh <python_script.py>

export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

# Run the Python script with all arguments
python "$@"
