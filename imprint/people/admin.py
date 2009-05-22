from django.contrib import admin
from people.models import Contributor

class ContributorAdmin(admin.ModelAdmin):
    fieldsets = ((None, {'fields': ['name']}),
                 ('Optional', {'fields': ['position', 'email', 'user']}))
    list_display = ['name', 'position', 'email']

admin.site.register(Contributor, ContributorAdmin)

