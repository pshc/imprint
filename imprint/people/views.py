from django.shortcuts import get_object_or_404
from people.models import *
from utils import renders

@renders('people/contributor_detail.html')
def contributor_detail(request, slug):
    object = get_object_or_404(Contributor, slug=slug)
    pieces = object.pieces.all()
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
