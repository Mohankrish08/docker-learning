#!/bin/sh
# ---------------------------------------------------------------
# One image. This script decides what the container becomes,
# based on the APP_ROLE environment variable passed at run time.
# ---------------------------------------------------------------
set -e

echo "Starting container with APP_ROLE=${APP_ROLE}"

case "$APP_ROLE" in
  api)
    # exec replaces the shell with gunicorn as PID 1,
    # so `docker stop` reaches the app instead of the shell.
    exec gunicorn --bind "0.0.0.0:${PORT:-5000}" \
                  --workers 2 \
                  --access-logfile - \
                  app.api:app
    ;;
  worker)
    exec python -u -m app.worker
    ;;
  *)
    echo "ERROR: APP_ROLE must be 'api' or 'worker', got '${APP_ROLE}'" >&2
    exit 1
    ;;
esac
