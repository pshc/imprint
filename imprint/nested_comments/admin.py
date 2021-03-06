from django.contrib import admin
from django.utils.html import conditional_escape
from nested_comments.models import NestedComment

class NestedCommentsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Content',
           {'fields': ('user', 'user_name', 'user_email', 'comment')}
        ),
        ('Metadata',
           {'fields': ('submit_date', 'ip_address', 'is_removed')}
        ),
     )

    list_display = ('comment_preview', 'poster_name', 'target', 'submit_date', 'is_removed')
    list_filter = ('submit_date', 'site', 'is_removed')
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    search_fields = ('comment', 'user_name', 'user_email', 'user_url', 'ip_address')
    actions = ['remove_comments']

    def remove_comments(self, request, queryset):
        n = queryset.update(is_removed=True)
        n = '1 comment was' if n == 1 else '%d comments were' % n
        self.message_user(request, n + ' successfully marked as removed.')
    remove_comments.short_description = "Remove selected comments"

    def comment_preview(self, obj):
        if len(obj.comment) > 45:
            return obj.comment[:42] + " ..."
        else:
            return obj.comment

    def target(self, obj):
        return '<a href="%s">%s</a>' % (obj.content_object.get_absolute_url(),
                conditional_escape(unicode(obj.content_object)))
    target.allow_tags = True

admin.site.register(NestedComment, NestedCommentsAdmin)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
