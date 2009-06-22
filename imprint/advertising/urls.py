from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('advertising.views',
    url(r'^redirect/(?P<id>\d+)/$', 'ad_redirect', name='ad-redirect'),
)

