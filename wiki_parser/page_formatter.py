import json
import re
from typing import List, Optional

from bs4 import BeautifulSoup, Tag


def _format_link(url: str) -> Optional[str]:
    """
    Formats links on wiki page
    :param url: href attribute of <a> element
    :return: if correct internal link, returns formatted link; otherwise (external or incorrect) returns `None`
    """
    # regex match
    match = re.fullmatch(r"^/wiki/([^/:]*)$", url)
    if match is None:
        return
    return match[1]


def wiki_format_html(html: str) -> str:
    """
    Formats html according to game rules
    :return: formatted html
    """
    # load html
    soup = BeautifulSoup(html, "html.parser")
    # get all links
    links: List[Tag] = soup.find_all("a")
    for link in links:
        # if no href, skip
        if "href" not in link.attrs:
            continue
        # INFO: various onclick and other link redirects are not formatted,
        #  as wikipedia doesn't use them

        # if href is a fragment, skip formatting
        if not link["href"] or link["href"][0] == "#":
            continue
        # format destination
        dest_page = _format_link(link["href"])
        # if formatting failed, delete link href
        if dest_page is None:
            del link["href"]
        else:
            # if formatting succeeded, leave link
            link["href"] = dest_page
            # add onclick listener to announce link click to parent window (as parsed html is accessed through an
            # iframe)
            obj = {"type": "click", "destination": dest_page}
            # TODO: check no injection is possible
            link["onclick"] = f"window.parent.postMessage({json.dumps(obj)}, '*')"
    # return formatted html
    return soup.prettify()
