#!/bin/sh
set -eu

if [ -n "${DATABASE_URL:-}" ] && [ -z "${DATABASE_URL_SYNC:-}" ]; then
  DATABASE_URL_SYNC=$(printf '%s' "${DATABASE_URL}" | sed 's#^postgresql+asyncpg://#postgresql+psycopg://#')
  export DATABASE_URL_SYNC
fi

if [ "${RUN_SEED_DATA:-false}" = "true" ]; then
  python -m backend.seed_data
fi

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
