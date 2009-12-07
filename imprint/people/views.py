from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from people.models import *
from issues.models import filter_live
from utils import renders

@renders('people/contributor_detail.html')
def contributor_detail(request, slug):
    object = get_object_or_404(Contributor, slug=slug)
    pieces = object.pieces.filter(**filter_live())
    return locals()

def contributor_email(request, slug, id):
    # Poor man's verification: require the contributor's matching ID
    object = get_object_or_404(Contributor, slug=slug, pk=int(id))
    return HttpResponse(object.email, mimetype='text/plain')

@permission_required('people.edit_contributor')
@renders('people/merge_contributors.html')
def merge_contributors(request, ids):
    admin_url = '/admin/people/contributor/'
    def message(msg):
        request.user.message_set.create(message=msg)
        return HttpResponseRedirect(admin_url)
    int_ids = map(int, ids.split(','))
    if len(set(int_ids)) != len(int_ids):
        return message(u'Duplicate contributors.')
    if len(int_ids) < 2:
        return message(u'Not enough contributors.')
    if request.method == 'POST':
        try:
            dest = Contributor.objects.get(pk=int(request.POST['dest']))
        except:
            return message(u'You need to select a target contributor.')
        try:
            int_ids = filter(lambda id: id != dest.id, int_ids)
            dest.merge_with(Contributor.objects.in_bulk(int_ids).itervalues())
        except Exception, e:
            return message(u"Couldn't merge: %s" % e)
        return message(u'Merged as %s.' % dest.name)
    objects = Contributor.objects.in_bulk(int_ids)
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
