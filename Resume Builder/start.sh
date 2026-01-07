#!/bin/sh
set -e

echo "Waiting for Postgres..."

until pg_isready -h resume-postgres -p 5432 -U postgres; do
  sleep 1
done

echo "Postgres is ready. Running migrations..."

alembic upgrade head

echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
