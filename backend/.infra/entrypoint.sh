#!/bin/sh

set -e
if [ "$FDUEL_MIGRATE" = "true" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
    echo "Clening locked fights before server starts..."
    python manage.py clean_locked_fights
fi

exec "$@"