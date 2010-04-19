from django import forms
from django.contrib import admin
from issues.models import *
from people.models import Contributor

class IssueForm(forms.ModelForm):
    model = Issue
    class Media:
        js = ('/media/js/jquery.js',
              '/media/js/jquery-ui.js',
              '/media/js/admin-sortable.js')
    class Meta:
        exclude = ('site',)

class IssueSectionInline(admin.StackedInline):
    model = IssueSection
    extra = 2
    verbose_name = 'Section'
    verbose_name_plural = 'Custom section header order (drag to reorder)'
    template = 'admin/inline_issue.html'

class IssueAdmin(admin.ModelAdmin):
    form = IssueForm
    inlines = (IssueSectionInline,)
    list_display = ['__unicode__', 'is_live']
    date_hierarchy = 'date'

class EditorshipInline(admin.TabularInline):
    model = SectionEditorship
    extra = 2

class SectionAdmin(admin.ModelAdmin):
    inlines = (EditorshipInline,)
    prepopulated_fields = {'slug': ('name',)}

def series_contributors(series):
    return ', '.join(unicode(c) for c in series.contributors.all())

class SeriesAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['__unicode__', 'slug', series_contributors]

admin.site.register(Issue, IssueAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Series, SeriesAdmin)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
