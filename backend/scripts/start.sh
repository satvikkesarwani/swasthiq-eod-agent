#!/usr/bin/env sh
set -eu

python3 -m alembic upgrade head
exec python3 -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}"
