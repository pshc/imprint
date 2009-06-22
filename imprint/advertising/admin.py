from django.contrib import admin
from advertising.models import ImageAd

class ImageAdAdmin(admin.ModelAdmin):
    fieldsets = ((None, {'fields': ['image', 'type', 'url']}),
                 ('Optional', {'fields': ['caption', 'client']}))
    list_display = ('image_filename', 'client', 'url', 'type', 'hits', 'is_active')
    list_filter = ('is_active', 'type')
    search_fields = ('image_filename', 'client', 'url', 'caption')
    actions = ('make_active', 'make_inactive')

    def make_active(self, request, queryset):
        n = queryset.update(is_active=True)
        msg = '1 ad was' if n == 1 else '%d ads were' % n
        self.message_user(request, msg + " activated.")

    def make_inactive(self, request, queryset):
        n = queryset.update(is_active=False)
        msg = '1 ad was' if n == 1 else '%d ads were' % n
        self.message_user(request, msg + " deactivated.")

admin.site.register(ImageAd, ImageAdAdmin)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
