import logging

import django.http
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

import wiki_app.views
from wiki_race.settings import USER_COOKIE_NAME
from wiki_app.data.db import get_user, _create_party, _join_party


def create_party_internal(request: HttpRequest) -> HttpResponse:
    user = get_user(request)
    try:
        party = _create_party(user, request.GET)
        response = redirect(wiki_app.views.game_page, game_id=party.uid)
    except Exception as e:
        logging.error(e)
        response = django.http.HttpResponseBadRequest()
    response.set_cookie(USER_COOKIE_NAME, user.uid)
    return response


def enter_party_internal(request: HttpRequest) -> HttpResponse:
    user = get_user(request)
    try:
        game_id = _join_party(user, request.GET)
        response = redirect(wiki_app.views.game_page, game_id=game_id)
    except:
        response = django.http.HttpResponseBadRequest()
    response.set_cookie(USER_COOKIE_NAME, user.uid)
    return response
