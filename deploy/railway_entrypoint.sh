#!/bin/sh
set -eu
if [ "${NIGHTWELL_APP_ROLE:-dev}" = "public" ]; then
    exec python deploy/ashfall_server.py
fi
exec sh deploy/start_railway.sh
