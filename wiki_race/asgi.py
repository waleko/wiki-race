"""
ASGI config for wiki_race project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

from wiki_app.websockets.urls import websocket_router

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wiki_race.settings")

application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP requests
        "http": get_asgi_application(),
        # WebSocket chat handler
        "websocket": websocket_router,
    }
)
