#!/usr/bin/env bash
# Create the tables and seed the catalog by hand (the backend also does this on startup).
# Usage (from repo root, venv active):  bash database/scripts/apply_schema.sh
set -euo pipefail
cd "$(dirname "$0")/../../backend"
python -m app.core.migrate
python -m app.catalog.seed
