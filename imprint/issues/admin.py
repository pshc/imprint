from django.contrib import admin
from issues.models import Issue

class IssueAdmin(admin.ModelAdmin):
    fields = ('date', 'number', 'volume')

admin.site.register(Issue, IssueAdmin)

