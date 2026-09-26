#!/bin/sh
# Waits for Postgres (when configured), applies migrations, then runs the given command (CMD).
set -e

if [ -n "$POSTGRES_HOST" ]; then
    echo "Waiting for Postgres at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
    until python -c "
import os, sys
import psycopg2
try:
    psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB', 'postgres'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', ''),
        host=os.environ['POSTGRES_HOST'],
        port=os.environ.get('POSTGRES_PORT', '5432'),
    )
except Exception:
    sys.exit(1)
"; do
        sleep 1
    done
    echo "Postgres is up."
fi

python manage.py migrate --noinput

exec "$@"
