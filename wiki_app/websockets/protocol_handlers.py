from typing import Callable, Dict

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
    def handler_decorator(func: Callable[[AsyncWebsocketConsumer, dict], None]):
        protocol_handlers[op_name] = func
    return handler_decorator
