from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'imprint.views.root'),
    (r'^accounts/profile/$', 'imprint.views.account_profile'),
    (r'^accounts/', include('django_authopenid.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
)

if settings.DEBUG:
    urlpatterns.append(url(r'^media/(.*)$', 'django.views.static.serve',
                           {'document_root': settings.MEDIA_ROOT,
                            'show_indexes': True}))
