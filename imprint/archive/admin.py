from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from archive.models import *

class PublicationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class PDFIssueAdmin(admin.ModelAdmin):
    pass

class PDFPageAdmin(admin.ModelAdmin):
    pass

admin.site.register(Publication, PublicationAdmin)
admin.site.register(PDFIssue, PDFIssueAdmin)
admin.site.register(PDFPage, PDFPageAdmin)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
