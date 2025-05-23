#!/usr/bin/env bash

set -euo pipefail

# Check the directory, should be root of the repository.

# Load the Python environment.
uv sync
# Go into target directory
cd gen-data

step=$((1024 * 64))
max=$((step * 15))

declare -a feat_types=("sort" "car" "zipf" "width")

for n_rows in $step $max; do
  for n_cols in 1 50 100; do
    for feat_type in "${feat_types[@]}"; do
      for feat_value in $(seq -f "%.1f" 0.0 0.1 1.0); do
        # Execute generation script
        file_name="data-${n_rows}-${n_cols}-${feat_type}-${feat_value}"

        if [ ! -e "$file_name" ]; then
          echo uv run gen_workloads.py float $n_rows $n_cols "$file_name" $feat_type $feat_value
        fi
      done
    done
  done
done | parallel -j 8

# Move all generations into one directory
mv data-* ../synth-data/csv
