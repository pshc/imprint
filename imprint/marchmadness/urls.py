from django.conf.urls.defaults import *

urlpatterns = patterns('marchmadness.views',
    url(r'^$', 'index', name='mm-index'),
    url(r'bracket/$', 'choose_picks', name='mm-choose-picks'),
    url(r'save-picks/$', 'save_picks', name='mm-save-picks'),
    url(r'edit-teams/$', 'edit_teams', name='mm-edit-teams'),
    url(r'login/$', 'login', name='mm-login'),
    url(r'join/$', 'create_account', name='mm-create-account'),
)

urlpatterns += patterns('django.views.generic.simple',
    url(r'^terms-and-conditions/$', 'direct_to_template',
        {'template': 'marchmadness/terms.html'}, name='mm-terms'),
)
