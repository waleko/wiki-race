#!/usr/bin/env sh
python manage.py migrate
python manage.py createcachetable
gunicorn wiki_race.asgi -k uvicorn.workers.UvicornWorker