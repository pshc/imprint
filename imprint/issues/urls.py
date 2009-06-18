from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('issues.views',
    url(r'^$', 'latest_issue', name='latest-issue'),
    url(r'^vol(?P<volume>\d+)/issue(?P<number>\d+)/$', 'issue_detail', name='issue-detail'),
    # Should be last
    url(r'^(?P<slug>[^/]+)/$', 'section_detail', name='section-detail'),
)

