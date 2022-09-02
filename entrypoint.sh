#!/usr/bin/env sh
python manage.py migrate
python manage.py createcachetable
python -m gunicorn wiki_race.asgi -k uvicorn.workers.UvicornWorker -b ":${PORT:-3001}"