from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render

from wiki_parser.page_formatter import wiki_format_html
from wiki_race.wiki_api.parse import load_wiki_page


def parse_article(request: HttpRequest, article: str) -> HttpResponse:
    article_info = load_wiki_page(article)
    if article_info is None:
        return HttpResponseNotFound()
    formatted_html = wiki_format_html(article_info.text)
    response = render(request, 'parsed-response.html', context={'mw_parser': formatted_html, 'headers': {'X-Frame-Options': 'allow'}})
    return response
