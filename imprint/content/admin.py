from content.models import *
from django.contrib import admin
class EditorshipInline(admin.TabularInline):
    model = SectionEditorship
    extra = 2

class SectionAdmin(admin.ModelAdmin):
    inlines = (EditorshipInline,)
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Section, SectionAdmin)
admin.site.register(Piece)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
