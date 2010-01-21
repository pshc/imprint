import couchdb
from django.conf import settings

class CouchDBImproperlyConfigured(Exception):
    pass

try:
    HOST = settings.COUCHDB_HOST
except AttributeError:
    raise CouchDBImproperlyConfigured("Please ensure that COUCHDB_HOST is "
            "set in your settings file.")

DATABASE_NAME = getattr(settings, 'COUCHDB_DATABASE_NAME',
        '') or settings.SITE_PREFIX
DESIGN_DOCNAME = getattr(settings, 'COUCHDB_DESIGN_DOCNAME',
        '') or (settings.SITE_PREFIX + '-design')

if not hasattr(settings, 'couchdb_server'):
    settings.couchdb_server = couchdb.client.Server(HOST)
server = settings.couchdb_server

if not hasattr(settings, 'couchdb_db'):
    try:
        settings.couchdb_db = server.create(DATABASE_NAME)
    except couchdb.client.PreconditionFailed:
        settings.couchdb_db = server[DATABASE_NAME]
db = settings.couchdb_db

def couchdb_view(name, **kwargs):
    return db.view('%s/%s' % (DESIGN_DOCNAME, name), **kwargs)

def get_resource_or_404(id):
    try:
        return db[id]
    except couchdb.client.ResourceNotFound:
        raise Http404

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
