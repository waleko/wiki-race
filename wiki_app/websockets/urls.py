from channels.routing import URLRouter
from django.urls import path

from wiki_app.websockets.consumers import GameConsumer

urlpatterns = [
    path("game_connect/<str:game_id>/<str:user_id>", GameConsumer.as_asgi(), name='game-websocket'),
]

websocket_router = URLRouter(urlpatterns)
