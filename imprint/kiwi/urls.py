from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('')

if settings.KIWI_API_CODE:
    urlpatterns += patterns('kiwi.views',
        url(r'^login/$', 'kiwi_login', name='kiwi-login'),
        url(r'^logout/$', 'kiwi_logout', name='kiwi-logout'),
        url(r'^postback/$', 'kiwi_postback', name='kiwi-postback'),
    )

