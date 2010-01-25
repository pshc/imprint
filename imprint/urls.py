from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import direct_to_template, redirect_to
from feeds import *

admin.autodiscover()

feeds = {
    'latest': LatestPieces,
    'section': LatestSectionPieces,
    'series': LatestSeriesPieces,
}

urlpatterns = patterns('',
    (r'^accounts/profile/$', 'imprint.views.account_profile'),
    (r'^accounts/', include('django_authopenid.urls')),
    (r'^admin/content/piece/', include('content.admin_urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^ads/', include('advertising.urls')),
    (r'^archive/', include('archive.urls')),
    (r'^comments/', include('nested_comments.urls')),
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^people/', include('people.urls')),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
	    {'feed_dict': feeds}),
    (r'^robots.txt$', direct_to_template, {'template': 'robots.txt',
                                           'mimetype': 'text/plain'}),
)

# Site-specific apps
urlpatterns += patterns('',
    (r'^2010/feds/', include('feds.urls')),
    (r'^feds', redirect_to, {'url': '/2010/feds/'}),
)

# Catch-all root patterns
urlpatterns += patterns('',
    (r'^', include('content.urls')),
    (r'^', include('static.urls')),
    # Must be last
    (r'^', include('issues.urls')),
)

if settings.DEBUG:
    urlpatterns.append(url(r'^media/(.*)$', 'django.views.static.serve',
                           {'document_root': settings.MEDIA_ROOT,
                            'show_indexes': True}))
# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
