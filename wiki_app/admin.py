from django.contrib import admin

# Register your models here.
from wiki_app.models import AdminRole, Party, PartyMember, User

admin.register(User, Party, PartyMember, AdminRole, site=admin.site)
