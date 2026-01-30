#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

python manage.py collectstatic --noinput --clear

# Run migrations only when explicitly requested (e.g., one-off job)
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate
fi
