from django.contrib import admin
from feds.models import *

class PositionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'website']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Position, PositionAdmin)
admin.site.register(Candidate, CandidateAdmin)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
