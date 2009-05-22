from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('content.views',
    (r'^(?P<y>\d{4})/(?P<m>\d\d?)/(?P<d>\d\d?)/(?P<section>[^/]+)/(?P<slug>[^/]+)/$', 'article_detail'),
)

