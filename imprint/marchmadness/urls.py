from django.conf.urls.defaults import *

urlpatterns = patterns('marchmadness.views',
    url(r'^$', 'index', name='marchmadness-index'),
)

