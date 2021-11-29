import logging
import random
import urllib.parse
from collections import namedtuple
from typing import Optional, Tuple, List

import requests

from wiki_race.settings import WIKI_API

Article = namedtuple("Article", ["title", "text", "properties"])


def load_wiki_page(title: str) -> Optional[Article]:
    """
    Loads HTML of the wiki page by its title
    :param title: page title
    :return: loaded page as named tuple of (title, text and properties)
    """
    # send request
    request = requests.get(
        WIKI_API,
        params={"action": "parse", "page": title, "format": "json", "redirects": True},
    ).json()
    # TODO: mobile enhancements
    # if loading failed return
    if "error" in request:
        logging.error(request["error"])
        return None
    # get result
    parser_result = request["parse"]
    return Article(
        parser_result["title"], parser_result["text"]["*"], parser_result["links"]
    )


def _get_random_title() -> str:
    """
    Gets title of a random wiki page
    """
    # send request
    request = requests.get(
        WIKI_API,
        params={
            "action": "query",
            "list": "random",
            "format": "json",
            "rnnamespace": 0,
        },
    ).json()
    # if request failed, raise error
    if "error" in request:
        raise ValueError(request["error"])
    # get result
    random_query = request["query"]["random"]
    return random_query[0]["title"]


def compare_titles(a: str, b: str) -> bool:
    """
    Compares two titles of wiki pages
    :return: true if titles lead to the same page, false otherwise
    """
    return urllib.parse.unquote(a).replace("_", " ") == urllib.parse.unquote(b).replace(
        "_", " "
    )


def _walk_titles_randomly(start: str, steps: int) -> Tuple[str, List[str]]:
    """
    Internal function for selecting a new wiki page title by walking from given page
    :param start: Title of starting wiki page
    :param steps: Amount of steps (link clicks to be made)
    :return: Tuple of end page title and list of all page titles between them (ends inclusive).
    """
    # current page
    cur_page = start
    # page clicks history
    stack = []
    # iteration count not to end up in an endless cycle,
    #  as sometimes pages don't have any links to be clicked
    iters = 0
    # seek new page
    while len(stack) != steps and iters < 2 * steps:
        iters += 1
        # send request
        resp = requests.get(
            WIKI_API,
            params={
                "action": "parse",
                "page": cur_page,
                "format": "json",
                "redirects": True,
                "prop": ["links"],
            },
        ).json()
        # if not successful
        if "parse" not in resp:
            # remove last page and try again
            if stack:
                cur_page = stack.pop()
            continue

        # get result
        parser_result = resp["parse"]
        # get namespace zero pages. "Namespace 0" means normal wiki pages. Read more:
        # https://en.wikipedia.org/wiki/Wikipedia:Namespace
        namespace_zero_links = list(
            filter(lambda x: x["ns"] == 0, parser_result["links"])
        )
        # choose next page randomly
        cur_page = random.choice(namespace_zero_links)["*"]
        # ban loops
        if cur_page in stack:
            continue
        # add to stack
        stack.append(cur_page)

    # if path was not built, raise error
    if len(stack) != steps:
        raise ValueError(f"couldn't get out of {start}!")
    # return path
    return cur_page, [start] + stack


def check_valid_transition(from_page: str, to_page: str) -> bool:
    """
    Checks whether `to_page` wiki page can be reached by clicking an internal link from `from_page` wiki page.
    Used for verifying user's wikirace solution.
    :return: true if reachable, false otherwise
    """
    # send request
    parser_result = requests.get(
        WIKI_API,
        params={
            "action": "parse",
            "page": from_page,
            "format": "json",
            "redirects": True,
            "prop": ["links"],
        },
    ).json()["parse"]
    # get all internal links
    for e in parser_result["links"]:
        # get only namespace 0 links, compare titles
        if e["ns"] == 0 and compare_titles(e["*"], to_page):
            return True

    # if nothing found, return false
    return False


RoundPackage = namedtuple("RoundPackage", ["start_page", "end_page", "solution"])


def generate_round(
    steps_for_seed: int = 6,
    steps_for_solution: int = 2,
    given_seed: Optional[str] = None,
) -> RoundPackage:
    """
    Generates round package: (start page, end page, and solution -- list of all pages between start and end with ends
    inclusive).
    :param steps_for_seed: Amount of link clicks from seed to start page
    :param steps_for_solution: Amount of link clicks from start page to end page
    :param given_seed: Optionally, will use this given seed instead of a random one
    :return: start page, end page, and solution
    """
    # attempts of generating package
    attempts = 0
    while attempts < 10:
        try:
            # get seed
            if given_seed:
                seed = given_seed
            else:
                seed = _get_random_title()

            # get start
            start, _ = _walk_titles_randomly(seed, steps_for_seed)
            # get end and solution
            dest, solution = _walk_titles_randomly(start, steps_for_solution)
            # return package
            return start, dest, solution
        except:
            # if failed, try again
            attempts += 1
    # if could not generate round (for instance, page has no internal links)
    raise ValueError("couldn't generate round!")
