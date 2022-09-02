FROM python:latest

ADD ./ /usr/local/wikirace
WORKDIR /usr/local/wikirace

RUN pip install -r requirements.txt

ENV DJANGO_SETTINGS_MODULE wiki_race.settings

ENTRYPOINT ["./entrypoint.sh"]