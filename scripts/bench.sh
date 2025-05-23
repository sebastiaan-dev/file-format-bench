#!/usr/bin/env bash

set -euo pipefail

# Go to target directory and load environment.
cd vortex/duckdb-vortex

# Not recommended, but for ease of use we auto-allow
direnv allow
eval "$(direnv export bash)"
BUILD_BENCHMARK=1 make release

cd ../..

# Go to target directory and load environment
cd duckdb-fastlanes

# Not recommended, but for ease of use we auto-allow
direnv allow
eval "$(direnv export bash)"
BUILD_BENCHMARK=1 make release

cd ..

# Remove old results
rm -rf benchmark/*
rm -rf results/raw/*

# Generate benchmarks
uv run generate_bench.py

./duckdb-fastlanes/build/release/benchmark/benchmark_runner --threads=8 --root-dir $(pwd) "benchmark/fls/.*" 2>&1 | tee results/raw/fls_results.csv

./vortex/duckdb-vortex/build/release/benchmark/benchmark_runner --threads=8 --root-dir $(pwd) "benchmark/vortex/.*" 2>&1 | tee results/raw/vortex_results.csv
./vortex/duckdb-vortex/build/release/benchmark/benchmark_runner --threads=8 --root-dir $(pwd) "benchmark/parquet/.*" 2>&1 | tee results/raw/parquet_results.csv
