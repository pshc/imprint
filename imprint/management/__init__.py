from django.db.models import signals
from content import COUCHDB_DESIGN_DOCNAME, db, models
from couchdb.design import ViewDefinition
from textwrap import dedent

VIEWS = []

def add_couchdb_view(name, code):
    VIEWS.append(ViewDefinition(COUCHDB_DESIGN_DOCNAME, name, dedent(code)))
def create_couchdb_views(app, created_models, verbosity, **kwargs):
    ViewDefinition.sync_many(db, VIEWS)
signals.post_syncdb.connect(create_couchdb_views, sender=models)

add_couchdb_view('by_date', """
    function (doc) {
        emit(doc.$PREFIX_date, null);
    }""")


# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
