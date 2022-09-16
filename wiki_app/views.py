from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from wiki_app.data.db import get_user, is_admin
from wiki_app.models import Party, PartyMember
from wiki_app.websockets import urls
from wiki_race.settings import (
    USER_COOKIE_NAME,
    MIN_TIME_LIMIT_SECONDS,
    MAX_TIME_LIMIT_SECONDS,
    USE_SECURE_WEBSOCKETS,
)


def index_view(request: HttpRequest) -> HttpResponse:
    """
    Index page view
    """
    return render(request, "index.html")


def new_party_page(request: HttpRequest) -> HttpResponse:
    """
    New lobby page view
    """
    return render(
        request,
        "create.html",
        context={
            "min_seconds": MIN_TIME_LIMIT_SECONDS,
            "max_seconds": MAX_TIME_LIMIT_SECONDS,
        },
    )


def join_page(request: HttpRequest, game_id: str) -> HttpResponse:
    """
    Join lobby page view
    """
    return render(request, "join.html", context={"game_id": game_id})


def game_page(request: HttpRequest, game_id: str) -> HttpResponse:
    """
    Main game view
    """
    # get user via cookie
    user = get_user(request)
    # get party object
    party = get_object_or_404(Party, uid=game_id)
    # check if user is already a party member
    member_present = PartyMember.objects.filter(party=party, user=user).count()
    if member_present == 0:
        # if no such member, redirect to join
        response = redirect(join_page, game_id=party.uid)
    else:
        # if already member, generate websocket url
        uri = reverse(
            "game-websocket",
            urlconf=urls,
            kwargs={"game_id": game_id, "user_id": user.uid},
        )
        websocket_protocol = "wss" if USE_SECURE_WEBSOCKETS else "ws"
        # load game page
        response = render(
            request,
            "game.html",
            context={
                "WEBSOCKET_URL": f"{websocket_protocol}://{request.get_host()}{uri}",
                "GAME_URL": f"{request.get_host()}{reverse('game-page', kwargs={'game_id': game_id})}",
                "is_admin": is_admin(party, user),
            },
        )
    # set user's cookie
    response.set_cookie(USER_COOKIE_NAME, user.uid)
    return response
