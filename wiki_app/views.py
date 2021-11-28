from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from wiki_app.data.db import get_user, is_admin
from wiki_app.models import Party, PartyMember
from wiki_app.websockets import urls
from wiki_race.settings import USER_COOKIE_NAME


def index_view(request: HttpRequest) -> HttpResponse:
    return render(request, "index.html")


def new_party_page(request: HttpRequest) -> HttpResponse:
    return render(request, "create.html")


def join_page(request: HttpRequest, game_id: str) -> HttpResponse:
    return render(request, "join.html", context={'game_id': game_id})


def game_page(request: HttpRequest, game_id: str) -> HttpResponse:
    user = get_user(request)
    party = get_object_or_404(Party, uid=game_id)

    member_present = PartyMember.objects.filter(party=party, user=user).count()
    if member_present == 0:
        response = redirect(join_page, game_id=party.uid)
    else:
        uri = reverse("game-websocket", urlconf=urls, kwargs={'game_id': game_id, 'user_id': user.uid})
        websocket_protocol = "ws" if request.get_host().startswith("127.0.0.1") else "wss"
        response = render(request, "game.html",
                          context={
                              "WEBSOCKET_URL": f"{websocket_protocol}://{request.get_host()}{uri}",
                              "is_admin": is_admin(party, user)
                          })

    response.set_cookie(USER_COOKIE_NAME, user.uid)
    return response
