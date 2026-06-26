#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs -0 -I {} echo {} || true)
fi

echo "==> Applying migrations..."
alembic upgrade head
echo "==> Done."