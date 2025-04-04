#!/bin/bash
# Script to update both Cargo.lock and poetry.lock files

set -e

echo "Updating Cargo.lock..."
cd fastapi_profiler/rustcore
cargo update -p fastapi-profiler-rust
cd ../..

echo "Updating poetry.lock..."
poetry lock --no-update

echo "Lock files updated successfully!"
