#!/usr/bin/env bash
set -euo pipefail

# --- CONFIG ---------------------------------------------------

# how many jobs to run in parallel?  (default: number of CPUs)
JOBS=${JOBS:-$(nproc)}

# path to your duckdb binary
DUCKDB_BIN="$(pwd)/vortex/duckdb-vortex/build/release/duckdb"

# make sure it's built
if [[ ! -x "$DUCKDB_BIN" ]]; then
  echo "Building duckdb..."
  cd vortex/duckdb-vortex
  # GEN=ninja make release   # uncomment if needed
  make release
  cd ../..
fi

# --- FUNCTION -------------------------------------------------

process_dataset() {
  local dataset="$1"
  # skip non-dirs or empty
  [[ ! -d "$dataset/gen_data" ]] && {
    echo "Skipping (no gen_data): $dataset"
    return
  }

  # find the CSV
  local csv_path
  csv_path=$(find "$dataset/gen_data" -maxdepth 1 -type f -name '*.csv' | head -n1)
  [[ -z "$csv_path" ]] && {
    echo "No CSV in $dataset/gen_data"
    return
  }

  local base
  base=$(basename "${csv_path%.*}")
  local vortex_out="synth-data/vortex/${base}.vortex"
  local parquet_out="synth-data/parquet/${base}.parquet"
  local fls_out="synth-data/fls/${base}.fls"

  # Vortex
  if [[ ! -e "$vortex_out" ]]; then
    echo "[${base}] → Vortex"
    "$DUCKDB_BIN" -c "COPY (SELECT * FROM read_csv('$csv_path')) TO '$vortex_out' (FORMAT VORTEX);"
  fi

  # Parquet
  if [[ ! -e "$parquet_out" ]]; then
    echo "[${base}] → Parquet"
    "$DUCKDB_BIN" -c "COPY (SELECT * FROM read_csv('$csv_path')) TO '$parquet_out' (FORMAT PARQUET);"
  fi

  # FLS
  if [[ ! -e "$fls_out" ]]; then
    echo "[${base}] → FLS"
    uv run main.py "$csv_path"
  fi
}

export -f process_dataset
export DUCKDB_BIN

# --- PARALLEL INVOCATION ---------------------------------------

# find all immediate subdirectories of synth-data/csv
find synth-data/csv -mindepth 1 -maxdepth 1 -type d |
  parallel -j "$JOBS" process_dataset {}
