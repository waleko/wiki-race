FROM python:latest

ADD ./ /usr/local/wikirace
WORKDIR /usr/local/wikirace

RUN pip install -r requirements.txt

RUN python manage.py migrate
RUN python manage.py createcachetable
ENTRYPOINT gunicorn wiki_race.asgi -k uvicorn.workers.UvicornWorker
# CMD bash