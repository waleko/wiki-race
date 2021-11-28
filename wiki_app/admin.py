from django.contrib import admin

# Register your models here.
from wiki_app.models import AdminRole, User, Party, PartyMember

admin.register(User, Party, PartyMember, AdminRole, site=admin.site)
