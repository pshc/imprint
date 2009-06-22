from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template

admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/profile/$', 'imprint.views.account_profile'),
    (r'^accounts/', include('django_authopenid.urls')),
    (r'^admin/content/piece/', include('content.admin_urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^ads/', include('advertising.urls')),
    (r'^comments/', include('nested_comments.urls')),
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^people/', include('people.urls')),
    (r'^robots.txt$', direct_to_template, {'template': 'robots.txt',
                                           'mimetype': 'text/plain'}),
    (r'^', include('content.urls')),
    # Must be last
    (r'^', include('issues.urls')),
)

if settings.DEBUG:
    urlpatterns.append(url(r'^media/(.*)$', 'django.views.static.serve',
                           {'document_root': settings.MEDIA_ROOT,
                            'show_indexes': True}))
