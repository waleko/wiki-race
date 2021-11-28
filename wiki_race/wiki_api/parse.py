import logging
import random
import urllib.parse
from collections import namedtuple
from typing import Optional, Tuple, List

import requests

from wiki_race.settings import WIKI_API

Article = namedtuple('Article', ['title', 'text', 'properties'])


def load_wiki_page(article: str) -> Optional[Article]:
    request = requests.get(WIKI_API,
                           params={'action': 'parse', 'page': article, 'format': 'json', 'redirects': True}
                           ).json()
    # TODO: mobile format
    if 'error' in request:
        logging.warning(request['error'])
        return None
    parser_result = request['parse']
    return Article(parser_result['title'], parser_result['text']['*'], parser_result['links'])


def get_random_title() -> str:
    random_query = requests.get(WIKI_API,
                                params={'action': 'query', 'list': 'random', 'format': 'json', 'rnnamespace': 0}
                                ).json()['query']['random']
    # TODO: null safety
    return random_query[0]['title']


def compare_titles(a: str, b: str) -> bool:
    return urllib.parse.unquote(a).replace('_', ' ') == urllib.parse.unquote(b).replace('_', ' ')


def walk_titles_randomly(start: str, steps: int) -> Tuple[str, List[str]]:
    cur_page = start
    stack = []
    iters = 0
    while len(stack) != steps and iters < 2 * steps:
        iters += 1

        resp = requests.get(WIKI_API,
                            params={'action': 'parse', 'page': cur_page, 'format': 'json', 'redirects': True,
                                    'prop': ['links']}
                            ).json()
        if 'parse' not in resp:
            if stack:
                cur_page = stack.pop()
            continue
        parser_result = resp['parse']
        category_zero_links = list(filter(lambda x: x['ns'] == 0, parser_result['links']))
        cur_page = random.choice(category_zero_links)['*']
        if cur_page in stack:
            continue
        stack.append(cur_page)
    if len(stack) != steps:
        raise ValueError(f"couldn't get out of {start}!")
    return cur_page, [start] + stack


def check_valid_transition(from_page: str, to_page: str) -> bool:
    parser_result = requests.get(WIKI_API,
                                 params={'action': 'parse', 'page': from_page, 'format': 'json', 'redirects': True,
                                         'prop': ['links']}
                                 ).json()['parse']
    for e in parser_result['links']:
        if e['ns'] == 0 and compare_titles(e['*'], to_page):
            return True
    return False


def generate_round(seed_walk: int = 8, solution_walk: int = 1, given_seed: Optional[str] = None) -> Tuple[str, str, List[str]]:
    attempts = 0
    while attempts < 10:
        try:
            if given_seed:
                seed = given_seed
            else:
                seed = get_random_title()

            start, _ = walk_titles_randomly(seed, seed_walk)
            dest, solution = walk_titles_randomly(start, solution_walk)
            return start, dest, solution
        except:
            attempts += 1
    raise ValueError("couldn't generate round!")
