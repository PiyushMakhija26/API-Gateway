#!/bin/sh
set -e

# Apply migrations first so a fresh free-tier database is ready on first boot.
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="*"
