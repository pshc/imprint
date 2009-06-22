from django.contrib import admin
from nested_comments.models import NestedComment

class NestedCommentsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Content',
           {'fields': ('user', 'user_name', 'user_email', 'user_url', 'comment')}
        ),
        ('Metadata',
           {'fields': ('submit_date', 'ip_address', 'is_public', 'is_removed')}
        ),
     )

    list_display = ('name', 'content_type', 'object_pk', 'ip_address', 'submit_date', 'is_public', 'is_removed')
    list_filter = ('submit_date', 'site', 'is_public', 'is_removed')
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    search_fields = ('comment', 'user__username', 'user_name', 
'user_email', 'user_url', 'ip_address')

admin.site.register(NestedComment, NestedCommentsAdmin)

