from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('content.views',
    (r'^$', 'piece_admin'),
    (r'^add/$', 'piece_create'),
    (r'^(\d+)/$', 'piece_change'),
    url(r'^contributor-lookup/(?P<with_position>with-position/)?$', 'contributor_lookup', name='admin-contributor-lookup'),
)

