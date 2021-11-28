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

from wiki_app.views import index_view, new_party_page, join_page, game_page
from wiki_parser.views import parse_article
from wiki_app.party.views import create_party_internal, enter_party_internal

urlpatterns = [
    path('wiki/<str:article>', parse_article),
    path('admin/', admin.site.urls),
    path('api/create', create_party_internal),
    path('api/enter', enter_party_internal),
    path('', index_view),
    path('new', new_party_page),
    path('join/<str:game_id>', join_page),
    path('game/<str:game_id>', game_page)
]
