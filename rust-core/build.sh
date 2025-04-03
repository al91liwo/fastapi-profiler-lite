#!/bin/bash
set -e

echo "Building fastapi-profiler-rust extension"

# Build and install with maturin
maturin develop --release

# Verify installation
python -c "from fastapi_profiler_rust import PyAggregatedStats; print('Extension successfully installed')"

echo "Build complete"
