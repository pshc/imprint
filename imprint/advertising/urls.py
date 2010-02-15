from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('advertising.views',
    url(r'^redirect/(?P<client>[\w-]+)/$', 'image_ad_redirect',
        name='image-ad-redirect'),
)

