#!/usr/bin/env bash
# Start without Docker (MySQL already running, DB created with database/init/000_create_database.sql).
# Phase 0: backend only. The frontend is added after M-2.
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] || { cp .env.example .env; echo "Created .env from .env.example - check DB_URL."; }

cd backend
if [ ! -d .venv ]; then python -m venv .venv; fi
if [ -f .venv/Scripts/activate ]; then source .venv/Scripts/activate; else source .venv/bin/activate; fi
pip install -q -r requirements.txt

# Startup applies database/schema/*.sql and seeds the catalog tables (DB_AUTO_INIT=true).
exec uvicorn app.main:app --reload --port "${API_PORT:-8000}"
