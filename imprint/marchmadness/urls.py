from django.conf.urls.defaults import *

urlpatterns = patterns('marchmadness.views',
    url(r'^$', 'index', name='mm-index'),
    url(r'save-picks/$', 'save_picks', name='mm-save-picks'),
)

