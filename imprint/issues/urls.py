from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('issues.views',
    url(r'^$', 'latest_issue', name='latest-issue'),
    url(r'^(\d{4})/(\d\d?)/(\d\d?)/$', 'issue_detail', name='issue-detail'),
    url(r'^(\d{4})/(\d\d?)/(\d\d?)/([^/]+)/$', 'section_detail', name='section-detail'),
    # Should be last
    url(r'^(?P<slug>[^/]+)/$', 'section_latest_issue', name='section-latest-issue'),
)

