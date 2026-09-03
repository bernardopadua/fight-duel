#!/bin/sh

set -e
if [ "$FDUEL_MIGRATE" = "true" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput

    echo "Cleaning locked fights before server starts..."
    python manage.py clean_locked_fights
    
    echo "Cleaning players stuck in worlds..."
    python manage.py clean_world_id_players
    
    echo "Cleaning players ws channels..."
    python manage.py clean_ws_user_channel
fi

exec "$@"