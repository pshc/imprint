from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from advertising.models import *
from utils import renders

@renders('advertising/image_ad_redirect.html')
def image_ad_redirect(request, client):
    object = get_object_or_404(ImageAd, client=client)
    object.hits += 1
    object.save()
    url = object.url
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
