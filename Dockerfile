FROM python:latest

ADD ./ /usr/local/wikirace
WORKDIR /usr/local/wikirace

RUN pip install -r requirements.txt
ENTRYPOINT /usr/local/wikirace/prod.sh
# CMD bash