#!/bin/sh
# start.sh

# Wait for Postgres to be ready
echo "Waiting for Postgres..."
until pg_isready -h db -p 5432 -U postgres; do
  sleep 1
done
echo "Postgres is ready!"

# Run Alembic migrations
alembic upgrade head

# Start FastAPI
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
