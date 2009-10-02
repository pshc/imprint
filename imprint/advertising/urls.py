from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('advertising.views',
    url(r'^redirect/(?P<client>[^/]+)/$', 'image_ad_redirect',
        name='image-ad-redirect'),
)

