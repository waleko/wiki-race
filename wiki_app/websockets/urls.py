import django
from channels.routing import URLRouter
from django.urls import path

django.setup()
# NOTICE: place this above import of consumers, as settings have not been initialized!

from wiki_app.websockets.consumers import GameConsumer

urlpatterns = [
    path("game_connect/<str:game_id>/<str:user_id>", GameConsumer.as_asgi(), name='game-websocket'),
]
"""
Websockets url patterns
"""

websocket_router = URLRouter(urlpatterns)
