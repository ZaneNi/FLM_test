#!/bin/bash

# Automatically run the FLM test script

set -e  # Exit on error

echo "======================================"
echo "Running FLM Test Suite"
echo "======================================"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the Python test script
echo "Starting test execution..."
python3 main.py

echo ""
echo "======================================"
echo "Test execution completed"
echo "======================================"
