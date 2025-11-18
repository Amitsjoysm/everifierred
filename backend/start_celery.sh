#!/bin/bash
cd /app/backend
exec /root/.venv/bin/celery -A celery_app worker --loglevel=info --logfile=/var/log/celery-worker.log
