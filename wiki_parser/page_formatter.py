import json
import re
from typing import List, Optional

from bs4 import BeautifulSoup, Tag


def filter_link(dest: str) -> Optional[str]:
    match = re.fullmatch(r"^/wiki/([^/:]*)$", dest)
    if match is None:
        return None
    return match[1]


def wiki_format_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    links: List[Tag] = soup.find_all('a')
    for link in links:
        if 'href' not in link.attrs:
            continue
        if not link['href'] or link['href'][0] == '#':
            continue
        dest_page = filter_link(link['href'])
        if dest_page is None:
            del link['href']
        else:
            obj = {"type": "click", "destination": dest_page}
            link['onclick'] = f"window.parent.postMessage({json.dumps(obj)}, '*')"  # TODO: check no injection is possible
    return soup.prettify()
