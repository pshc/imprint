from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('content.views',
    (r'^$', 'piece_admin'),
    (r'^add/$', 'piece_create'),
    (r'^contributor-lookup/$', 'contributor_lookup'),
)

