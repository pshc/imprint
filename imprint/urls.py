from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/profile/$', 'imprint.views.account_profile'),
    (r'^accounts/', include('django_authopenid.urls')),
    (r'^admin/content/piece/', include('content.admin_urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^people/', include('people.urls')),
    (r'^', include('content.urls')),
    # Must be last
    (r'^', include('issues.urls')),
)

if settings.DEBUG:
    urlpatterns.append(url(r'^media/(.*)$', 'django.views.static.serve',
                           {'document_root': settings.MEDIA_ROOT,
                            'show_indexes': True}))
