from django.contrib import admin
from issues.models import Issue, Section, SectionEditorship

class IssueAdmin(admin.ModelAdmin):
    fields = ('date', 'is_live', 'number', 'volume', 'sections')
    filter_horizontal = ['sections']

class EditorshipInline(admin.TabularInline):
    model = SectionEditorship
    extra = 2

class SectionAdmin(admin.ModelAdmin):
    inlines = (EditorshipInline,)
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Issue, IssueAdmin)
admin.site.register(Section, SectionAdmin)

