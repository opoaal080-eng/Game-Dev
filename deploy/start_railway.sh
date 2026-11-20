#!/bin/sh
set -eu

# Production requires either PostgreSQL or SQLite on the mounted persistent volume.
if [ -z "${DATABASE_URL:-}" ] && [ "${SQLITE_PATH:-}" != "/data/db/dev.sqlite3" ]; then
    echo "ERROR: set DATABASE_URL (Postgres) or SQLITE_PATH=/data/db/dev.sqlite3" >&2
    exit 1
fi

# For persistent file uploads, mount a Railway Volume to /data.
if [ "${PRIVATE_UPLOAD_ROOT:-}" != "/data/private_uploads" ] || [ ! -d /data ]; then
    echo "ERROR: attach a Railway volume mounted at /data and set PRIVATE_UPLOAD_ROOT=/data/private_uploads" >&2
    exit 1
fi

mkdir -p "${PRIVATE_UPLOAD_ROOT}"

python manage.py migrate --noinput
python manage.py bootstrap_admin
python manage.py bootstrap_developers
python manage.py replace_developers
python manage.py collectstatic --noinput
exec gunicorn nightwell_dev.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --access-logfile - --error-logfile -
