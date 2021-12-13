from typing import Callable

import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer


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
            async with aiohttp.ClientSession() as session:
                await func(a, b, session)

        protocol_handlers[op_name] = myfunc

    return handler_decorator
