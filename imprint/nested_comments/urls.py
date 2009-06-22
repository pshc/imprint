from django.conf.urls.defaults import *

urlpatterns = patterns('nested_comments.views',
    url(r'^reply/(\d+)/$', 'reply', name='nested-comments-reply'),
)

