from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from people.models import Contributor

class ContributorAdmin(admin.ModelAdmin):
    fieldsets = ((None, {'fields': ['name']}),
                 ('Optional', {'fields': ['position', 'email', 'user']}))
    list_display = ['name', 'position', 'email']
    actions = ['merge_selected_contributors']

    def merge_selected_contributors(self, request, queryset):
        ids = queryset.values_list('id', flat=True)
        if len(ids) < 2:
            self.message_user(request, "You must select at least two users.")
        else:
            return redirect('merge-contributors', ','.join(map(str, ids)))

admin.site.register(Contributor, ContributorAdmin)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
