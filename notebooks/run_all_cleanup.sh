#!/usr/bin/env bash
# Run all GDELT cleanup notebooks in the recommended full-reset order:
#   02 (property graph) → 03 (incremental artifacts) → 04 (Dataplex + descriptions) → 01 (datasets + local exports)
#
# Usage:
#   cd notebooks && ./run_all_cleanup.sh
#   # or from repo root:
#   bash notebooks/run_all_cleanup.sh
#
# Requires: Jupyter / nbconvert (pip install jupyter) and GCP credentials configured for the project in notebooks/config.py.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANUP_DIR="$SCRIPT_DIR/clean_up"

OUTDIR="$(mktemp -d "${TMPDIR:-/tmp}/gdelt_cleanup_execute.XXXXXX")"
echo "Writing executed notebooks to: $OUTDIR"
echo ""

NOTEBOOKS=(
  "02_gdelt_graph_create_cleanup.ipynb"
  "03_gdelt_incremental_refresh_cleanup.ipynb"
  "04_gdelt_data_profiling_cleanup.ipynb"
  "01_gdelt_data_prep_cleanup.ipynb"
)

# Use the same interpreter as your environment (e.g. repo venv): `PYTHON=../../venv/bin/python3 ./run_all_cleanup.sh`
PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" -m jupyter nbconvert --version >/dev/null 2>&1; then
  echo "error: Jupyter nbconvert not available for: $PYTHON" >&2
  echo "      Fix: activate the project venv and pip install nbconvert   (or: pip install -r requirements.txt)" >&2
  exit 1
fi

for nb in "${NOTEBOOKS[@]}"; do
  nb_path="$CLEANUP_DIR/$nb"
  if [[ ! -f "$nb_path" ]]; then
    echo "error: missing $nb (expected under $CLEANUP_DIR)" >&2
    exit 1
  fi
  echo "========== Executing $nb =========="
  "$PYTHON" -m jupyter nbconvert \
    --to notebook \
    --execute "$nb_path" \
    --output-dir="$OUTDIR" \
    --output="${nb%.ipynb}.executed" \
    --ExecutePreprocessor.timeout="${CLEANUP_NB_TIMEOUT:-3600}"
  echo ""
done

echo "All cleanup notebooks finished successfully."
echo "Executed copies (with cell outputs): $OUTDIR"
