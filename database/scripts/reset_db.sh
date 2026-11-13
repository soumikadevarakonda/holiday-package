#!/usr/bin/env bash
# DEV ONLY: drop and recreate the `holiday` database, then rebuild tables and catalog.
# Needs the MySQL root password. Usage:  bash database/scripts/reset_db.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
mysql -u root -p -e "DROP DATABASE IF EXISTS holiday;"
mysql -u root -p < "$ROOT/database/init/000_create_database.sql"
bash "$ROOT/database/scripts/apply_schema.sh"
