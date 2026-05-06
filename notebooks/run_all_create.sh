#!/usr/bin/env bash
# Run all GDELT pipeline notebooks in create order (builds BigQuery resources end-to-end):
#   01 (data prep + tables + procedures) → 02 (property graph) → 03 (incremental refresh) → 04 (Dataplex profiling + descriptions)
#
# Usage (from this directory):
#   ./run_all_create.sh
# or from repo root:
#   bash notebooks/run_all_create.sh
#
# Use the project venv interpreter, e.g.:
#   PYTHON=../venv/bin/python3 ./run_all_create.sh
#
# Requires: nbconvert (see repo requirements.txt), GCP credentials, and config.py (GCP_PROJECT_ID, etc.).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OUTDIR="$(mktemp -d "${TMPDIR:-/tmp}/gdelt_create_execute.XXXXXX")"
echo "Writing executed notebooks to: $OUTDIR"
echo ""

NOTEBOOKS=(
  "01_gdelt_data_prep.ipynb"
  "02_gdelt_graph_create.ipynb"
  "03_gdelt_incremental_refresh.ipynb"
  "04_gdelt_data_profiling.ipynb"
)

PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" -m jupyter nbconvert --version >/dev/null 2>&1; then
  echo "error: Jupyter nbconvert not available for: $PYTHON" >&2
  echo "      Fix: pip install nbconvert  (or: pip install -r requirements.txt from repo root)" >&2
  exit 1
fi

for nb in "${NOTEBOOKS[@]}"; do
  if [[ ! -f "$nb" ]]; then
    echo "error: missing $nb (expected under $SCRIPT_DIR)" >&2
    exit 1
  fi
  echo "========== Executing $nb =========="
  "$PYTHON" -m jupyter nbconvert \
    --to notebook \
    --execute "$nb" \
    --output-dir="$OUTDIR" \
    --output="${nb%.ipynb}.executed" \
    --ExecutePreprocessor.timeout="${CREATE_NB_TIMEOUT:-3600}"
  echo ""
done

echo "All create notebooks finished successfully."
echo "Executed copies (with cell outputs): $OUTDIR"
