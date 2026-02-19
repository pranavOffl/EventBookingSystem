#!/bin/sh
set -e

# Run database migrations
echo "Running migrations..."
uv run alembic upgrade head

# Start the application
echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
