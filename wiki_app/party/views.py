import logging

import django.http
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

import wiki_app.views
from wiki_app.data.db import create_party, get_user, join_party
from wiki_race.settings import USER_COOKIE_NAME


def api_create_party(request: HttpRequest) -> HttpResponse:
    """
    API view for creating a party.
    """
    # get user from cookie
    user = get_user(request)
    try:
        # try to create party
        party = create_party(user, request.GET.dict())
        # redirect host to game page
        response = redirect(wiki_app.views.game_page, game_id=party.uid)
    except Exception as e:
        logging.error(e)
        response = django.http.HttpResponseBadRequest()
    # set user cookie
    response.set_cookie(USER_COOKIE_NAME, user.uid)
    return response


def api_enter_party(request: HttpRequest) -> HttpResponse:
    """
    API view for joining party
    """
    # get user from cookie
    user = get_user(request)
    try:
        # try to join party
        party = join_party(user, request.GET.dict())
        # redirect host to game page
        response = redirect(wiki_app.views.game_page, game_id=party.uid)
    except Exception as e:
        logging.error(e)
        response = django.http.HttpResponseBadRequest()
    # set user cookie
    response.set_cookie(USER_COOKIE_NAME, user.uid)
    return response
