#!/usr/bin/env bash
set -e
echo "==> Running migrations + seeding plans..."
python scripts/render_migrate.py
echo "==> Starting web service on port ${PORT:-8080}..."
exec uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --timeout-keep-alive 75