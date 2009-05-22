from django.contrib import admin
from content.models import Article, ArticleAuthor, Section, SectionEditorship

class AuthorInline(admin.TabularInline):
    model = ArticleAuthor
    extra = 2

class ArticleAdmin(admin.ModelAdmin):
    fieldsets = ((None, {'fields': ('title', 'slug', 'deck', 'text')}),
                 ('Placement', {'fields': ('section', 'issue')}),
                 ('Misc', {'fields': ('sources', 'live')}))
    inlines = (AuthorInline,)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title']
    list_display = ['title', 'author_names', 'section', 'issue', 'live']
    list_filter = ['issue', 'section', 'live']

class EditorshipInline(admin.TabularInline):
    model = SectionEditorship
    extra = 2

class SectionAdmin(admin.ModelAdmin):
    inlines = (EditorshipInline,)
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Article, ArticleAdmin)
admin.site.register(Section, SectionAdmin)

