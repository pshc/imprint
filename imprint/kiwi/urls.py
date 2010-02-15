from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('kiwi.views',
url(r'^login/$', 'kiwi_login', name='kiwi-login'),
url(r'^logout/$', 'kiwi_logout', name='kiwi-logout'),
url(r'^postback/$', 'kiwi_postback', name='kiwi-postback'),
)

if settings.DEBUG:
    urlpatterns += patterns('kiwi.views',
	url(r'^toggle/$', 'kiwi_toggle'))
