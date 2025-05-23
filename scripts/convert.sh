#!/usr/bin/env bash

set -euo pipefail
# Go to target directory
cd vortex/duckdb-vortex
# Build the release binary (if this has not been done already)
# GEN=ninja make release

cd ../..
# Loop over all existing datasets
for dataset in synth-data/csv/*; do
  # Ignore if not a directory.
  if [ ! -d "$dataset" ]; then
    continue
  fi
  # Ignore if dataset is empty
  if [[ ! -d "$dataset/gen_data" ]]; then
    echo "Dataset is empty for: $dataset/gen_data"
    continue
  fi

  # Get the CSV file containing the actual data.
  csv_file_path=$(find $dataset/gen_data -maxdepth 1 -type f -name '*.csv' | head -n1)
  if [[ ! -e "$csv_file_path" ]]; then
    echo "Could not find CSV file for: $dataset/gen_data"
    continue
  fi

  csv_file="${csv_file_path##*/}"
  file_name="${csv_file%.*}"

  # Generate a Vortex file based on the CSV file.
  vortex_target="synth-data/vortex/$file_name.vortex"
  sql_vortex="COPY (SELECT * FROM read_csv('$csv_file_path')) TO '$vortex_target' (FORMAT VORTEX);"
  # Generate a Parquet file based on the CSV file.
  parquet_target="synth-data/parquet/$file_name.parquet"
  sql_parquet="COPY (SELECT * FROM read_csv('$csv_file_path')) TO '$parquet_target' (FORMAT PARQUET);"

  fls_target="synth-data/fls/$file_name.fls"

  # Execute DuckDB to create Vortex files.
  if [[ ! -e "$vortex_target" ]]; then
    echo "Generating: $vortex_target"
    ./vortex/duckdb-vortex/build/release/duckdb -c "$sql_vortex"
  fi

  # Execute DuckDB to create Parquet files.
  if [[ ! -e "$parquet_target" ]]; then
    echo "Generating: $parquet_target"
    ./vortex/duckdb-vortex/build/release/duckdb -c "$sql_parquet"
  fi

  # Execute Python script to generate FastLanes files.
  if [[ ! -e "$fls_target" ]]; then
    echo "Generating: $fls_target"
    uv run main.py $csv_file_path
  fi

done
