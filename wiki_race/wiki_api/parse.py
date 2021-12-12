import logging
import random
import urllib.parse
from collections import namedtuple
from typing import Optional, Tuple, List

import aiohttp
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


async def _get_next_page(cur_page: str, walk_backwards: bool) -> Optional[str]:
    """
    Gets random adjacent wiki page.
    """
    prop = "linkshere" if walk_backwards else "links"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            WIKI_API,
            params={
                "action": "query",
                "titles": cur_page,
                "format": "json",
                "prop": [prop],
            },
        ) as resp:
            data = await resp.json()
            # if not successful
            if "query" not in data:
                return
            # get result
            parser_result = list(data["query"]["pages"].values())[0]
            # get namespace zero pages. "Namespace 0" means normal wiki pages. Read more:
            # https://en.wikipedia.org/wiki/Wikipedia:Namespace
            namespace_zero_links = list(
                filter(lambda x: x["ns"] == 0, parser_result[prop])
            )
            # choose next page randomly
            return random.choice(namespace_zero_links)["title"]


async def _walk_titles_randomly(
    start: str, steps: int, walk_backwards: bool = False
) -> Tuple[str, List[str]]:
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
        next_page: str = await _get_next_page(cur_page, walk_backwards)
        # check result
        if not next_page:
            # remove last page and try again
            if stack:
                cur_page = stack.pop()
            continue
        # ban loops
        if next_page in stack:
            continue
        # add to stack
        stack.append(next_page)
        cur_page = next_page
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


async def solve_round(origin_page: str, target_page: str) -> Optional[List[str]]:
    """
    Solves round, i.e. traverses from origin to target
    :return: list of wiki page titles from origin to target page, or `None` if solution not found
    """
    try:
        origin_page, prequel = await _walk_titles_randomly(
            origin_page, 2, walk_backwards=False
        )
        target_page, sequel = await _walk_titles_randomly(
            target_page, 2, walk_backwards=True
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.sixdegreesofwikipedia.com/paths",  # TODO: devise a better solution
                json={"source": origin_page, "target": target_page},
            ) as resp:
                if not resp.ok:
                    raise ValueError(resp.reason)
                data = await resp.json()
                pages = data["pages"]
                paths = data["paths"]
                if not paths:
                    raise ValueError(f"paths empty: {origin_page} -> {target_page}")
                path = paths[0]
                solution: List[str] = []
                for num in path:
                    if str(num) not in pages:
                        raise ValueError(
                            f"{num} not in pages of {origin_page} -> {target_page}"
                        )
                    solution.append(pages[str(num)]["title"])
                full_solution = prequel[:-1] + solution + sequel[:-1][::-1]
                print(prequel, solution, sequel)
                print(full_solution)
                return full_solution
    except Exception as e:
        logging.warning(f"Unable to solve: {origin_page} -> f{target_page}", exc_info=e)
        return


def check_page_exists(page: str) -> bool:
    """
    Checks whether wiki page with given title exists
    """
    parser_result = requests.get(
        WIKI_API,
        params={"action": "query", "prop": "info", "titles": page, "format": "json"},
    ).json()
    try:
        return "-1" not in parser_result["query"]["pages"]
    except KeyError:
        return False
