from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from archive.models import *

class PublicationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Publication, PublicationAdmin)
admin.site.register(PDFIssue)
admin.site.register(PDFFile)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
