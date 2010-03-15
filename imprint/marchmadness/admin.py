from django.contrib import admin
from marchmadness.models import *

class TeamAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Team, TeamAdmin)
admin.site.register(Contestant)
admin.site.register(Match)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
