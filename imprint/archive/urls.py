from django.conf.urls.defaults import *

urlpatterns = patterns('archive.views',
    url(r'^$', 'archive_index', name='archive-index'),
    url(r'^(\d{4})/$', 'archive_year', name='archive-year'),
    url(r'^(\d{4})/(\w{3})/$', 'archive_month', name='archive-month'),
    url(r'^(\d{4})/(\w{3})/(\d\d?)/([\w-]+)/$', 'pdfissue_detail',
            name='pdfissue-detail'),
    url(r'^(\d{4})/(\w{3})/(\d\d?)/([\w-]+)/thumbnail/$', 'pdfissue_thumbnail',
            name='pdfissue-thumbnail'),
    url(r'^(\d{4})/(\w{3})/(\d\d?)/([\w-]+)/page(\d+)/$', 'pdfpage_detail',
            name='pdfpage-detail'),
    url(r'^(\d{4})/(\w{3})/(\d\d?)/([\w-]+)/page(\d+)/thumbnail/$',
            'pdfpage_thumbnail', name='pdfpage-thumbnail'),
)

