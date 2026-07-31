#!/usr/bin/env sh
set -eu

export APP_ENV="${APP_ENV:-production}"
export LOG_FORMAT="${LOG_FORMAT:-json}"
export DATABASE_URL="${DATABASE_URL:-sqlite:////tmp/swasthiq_eod.db}"
export PORT="${PORT:-8080}"

echo "Starting SwasthiQ backend on port ${PORT}"
echo "Using database URL scheme: $(printf '%s' "${DATABASE_URL}" | sed 's/:.*$/:*** redacted/')"

python3 -m alembic upgrade head
exec python3 -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port "${PORT}"
