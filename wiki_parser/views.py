from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import render

from wiki_parser.page_formatter import wiki_format_html
from wiki_race.wiki_api.parse import load_wiki_page


def parse_wiki_page(request: HttpRequest, page_title: str) -> HttpResponse:
    """
    View that gets wiki page html and formats it according to game rules (removes external links, etc.)
    """
    # get wiki page data
    page_info = load_wiki_page(page_title)
    # if failed, return not found
    if page_info is None:
        return HttpResponseNotFound()
    # format html
    formatted_html = wiki_format_html(page_info.text)
    # respond with page
    response = render(request, 'parsed-response.html', context={'mw_parser': formatted_html, 'headers': {'X-Frame-Options': 'allow'}})
    return response
