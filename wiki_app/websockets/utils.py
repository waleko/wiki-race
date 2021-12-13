from typing import Tuple

import aiohttp

from wiki_race.wiki_api.parse import check_page_exists, compare_titles


async def check_new_round_route(
    data: dict, session: aiohttp.ClientSession
) -> Tuple[str, str]:
    # make round package
    start = data["origin"]
    end = data["target"]
    if await compare_titles(start, end, session):
        raise ValueError("Start and end pages must be different!")
    if not await check_page_exists(start, session):
        raise ValueError(f"Start page {start} doesn't exist")
    if not await check_page_exists(end, session):
        raise ValueError(f"End page {end} doesn't exist")
    return start, end
