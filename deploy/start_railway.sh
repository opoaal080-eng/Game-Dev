#!/bin/sh
set -eu

# Never run a writable production portal on an ephemeral SQLite database.
if [ -z "${DATABASE_URL:-}" ]; then
    echo "ERROR: DATABASE_URL must point to a persistent PostgreSQL database." >&2
    exit 1
fi

# For persistent file uploads, mount a Railway Volume to /data.
if [ "${PRIVATE_UPLOAD_ROOT:-}" != "/data/private_uploads" ] || [ ! -d /data ]; then
    echo "ERROR: attach a Railway volume mounted at /data and set PRIVATE_UPLOAD_ROOT=/data/private_uploads" >&2
    exit 1
fi

mkdir -p "${PRIVATE_UPLOAD_ROOT}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn nightwell_dev.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --access-logfile - --error-logfile -
