#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Creating initial data..."
python init_db.py
