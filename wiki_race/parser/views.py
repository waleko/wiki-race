from django.http import HttpRequest
from django.shortcuts import render

from wiki_race.parser.page_formatter import wiki_format_html
from wiki_race.wiki_api.parse import load_wiki_article


def parse_article(request: HttpRequest, article: str):
    article_info = load_wiki_article(article)
    formatted_html = wiki_format_html(article_info.text)
    return render(request, 'parsed-response.html', context={'mw_parser': formatted_html})
