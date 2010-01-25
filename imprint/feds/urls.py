from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('feds.views',
    url(r'^$', 'feds_index', name='feds-index'),
)

