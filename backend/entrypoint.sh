#!/bin/sh
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete. Starting server..."
exec gunicorn app.main:app -c gunicorn.conf.py
