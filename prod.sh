#!/usr/bin/env sh
gunicorn wiki_race.asgi -k uvicorn.workers.UvicornWorker