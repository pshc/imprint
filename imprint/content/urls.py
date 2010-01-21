from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('content.views',
    url(r'^(?P<y>\d{4})/(?P<m>\w{3})/(?P<d>\d\d?)/(?P<section>[^/]+)/(?P<slug>[^/]+)/$', 'piece_detail', name='piece-detail'),
    url(r'^(?P<y>\d{4})/(?P<m>\w{3})/(?P<d>\d\d?)/(?P<section>[^/]+)/(?P<slug>[^/]+)/(?P<image>[^/]+[.]\w{3,4})$', 'image_detail', name='image-detail'),
    url(r'^design$', 'piece_design', name='piece-design'),
    url(r'^design/convert$', 'design_convert_doc', name='design-convert-doc'),
    url(r'^couchdb/$', 'couchdb_index'),
    url(r'^couchdb/create/$', 'couchdb_create'),
    url(r'^couchdb/(?P<slug>[^/]+)/$', 'couchdb_piece'),
)

