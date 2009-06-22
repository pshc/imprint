from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from advertising.models import *

def ad_redirect(request, id):
    object = get_object_or_404(ImageAd, id=int(id))
    # TODO: Track uniques, use async queue
    object.hits += 1
    object.save()
    return HttpResponseRedirect(object.url)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
