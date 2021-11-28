import json
import logging
from typing import Callable, Dict

from channels.generic.websocket import AsyncWebsocketConsumer


protocol_handlers = {}


def protocol_handler(op_name: str):
    def handler_decorator(func: Callable[[AsyncWebsocketConsumer, dict], None]):
        protocol_handlers[op_name] = func
    return handler_decorator

