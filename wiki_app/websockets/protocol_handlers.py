from typing import Callable

import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer

from wiki_race.settings import AIOHTTP_SESSION

protocol_handlers = {}
"""
Dict of consumer handlers
"""


def protocol_handler(op_name: str):
    """
    Decorator for registering action handlers for `GameConsumer`
    :param op_name: action name
    """

    def handler_decorator(
        func: Callable[[AsyncWebsocketConsumer, dict, aiohttp.ClientSession], None]
    ):
        async def myfunc(a: AsyncWebsocketConsumer, b: dict):
            if AIOHTTP_SESSION:
                await func(a, b, AIOHTTP_SESSION)
            else:
                async with aiohttp.ClientSession() as session:
                    await func(a, b, session)
        protocol_handlers[op_name] = myfunc

    return handler_decorator
