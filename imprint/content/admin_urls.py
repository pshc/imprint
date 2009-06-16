from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('content.views',
    (r'^$', 'piece_admin'),
    (r'^add/$', 'piece_create'),
    url(r'^contributor-lookup/$', 'contributor_lookup', name='admin-contributor-lookup'),
)

