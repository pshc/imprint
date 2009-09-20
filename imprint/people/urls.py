from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('people.views',
    #url(r'^$', 'editorial_board'),
    url(r'^(?P<slug>[^/]+)/$', 'contributor_detail',
	    name='contributor-detail'),
    url(r'^(?P<slug>[^/]+)/email(?P<id>\d+)$', 'contributor_email',
	    name='contributor-email'),
)

