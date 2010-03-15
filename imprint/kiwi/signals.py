from django.conf import settings
from django.contrib.comments.signals import comment_will_be_posted
from kiwi.views import kiwi_preferred_name

def kiwi_verification(sender, comment, request, **kwargs):
    comment.kiwi_verified = False
    if 'kiwi_info' in request.session:
        comment.name = kiwi_preferred_name(request)
        comment.email = request.session['kiwi_info']['email']
        comment.kiwi_verified = True
    return True

if getattr(settings, 'KIWI_API_CODE', False):
    comment_will_be_posted.connect(kiwi_verification)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
