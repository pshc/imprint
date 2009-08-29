from django.conf.urls.defaults import *

urlpatterns = patterns('django.views.generic.simple',
	url(r'^about/$', 'direct_to_template',
		{'template': 'static/about.html'}, name='static-about'),
	url(r'^volunteer/$', 'direct_to_template',
		{'template': 'static/volunteer.html'}, name='static-volunteer'),
	url(r'^contact/$', 'direct_to_template',
		{'template': 'static/contact.html'}, name='static-contact'),
	url(r'^jobs/$', 'direct_to_template',
		{'template': 'static/jobs.html'}, name='static-jobs'),
)

