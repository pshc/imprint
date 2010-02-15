from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('people.views',
    #url(r'^$', 'editorial_board'),
    url(r'^merge/((?:\d+,)+\d+)$', 'merge_contributors',
	    name='merge-contributors'),
    # These should be last
    url(r'^(?P<slug>[\w-]+)/$', 'contributor_detail',
	    name='contributor-detail'),
    url(r'^(?P<slug>[\w-]+)/email(?P<id>\d+)$', 'contributor_email',
	    name='contributor-email'),
)

