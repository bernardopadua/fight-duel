#!/bin/sh

set -e
if [ "$FDUEL_MIGRATE" = "true" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
fi

exec "$@"