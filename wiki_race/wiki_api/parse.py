from collections import namedtuple

import requests

from wiki_race.settings import WIKI_API

Article = namedtuple('Article', ['title', 'text', 'properties'])


def load_wiki_article(article: str) -> Article:
    parser_result = requests.get(WIKI_API,
                                 params={'action': 'parse', 'page': article, 'format': 'json', 'redirects': True}
                                 ).json()['parse']
    return Article(parser_result['title'], parser_result['text']['*'], parser_result['links'])
