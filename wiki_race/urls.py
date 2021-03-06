"""wiki_race URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from wiki_app.views import index_view, new_party_page, join_page, game_page
from wiki_parser.views import parse_wiki_page
from wiki_app.party.views import api_create_party, api_enter_party

urlpatterns = [
    path("wiki/<str:page_title>", parse_wiki_page),
    path("admin/", admin.site.urls),
    path("api/create", api_create_party),
    path("api/enter", api_enter_party),
    path("", index_view),
    path("new", new_party_page),
    path("join/<str:game_id>", join_page),
    path("game/<str:game_id>", game_page, name="game-page"),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/logo/favicon.ico", permanent=True),
    ),
]
