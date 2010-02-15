from django.conf import settings
from django.contrib.comments.signals import comment_will_be_posted

def kiwi_verification(sender, comment, request, **kwargs):
    comment.kiwi_verified = False
    if 'kiwi_name_format' in request.POST:
        kiwi = request.session.get('kiwi_info', None)
        if kiwi:
            format = request.POST.get('kiwi_name_format')
            if format == 'firstlast':
                comment.name = kiwi['firstlastname']
                request.session['kiwi_name_pref'] = 'firstlast'
            elif format == 'full':
                comment.name = kiwi['name']
                request.session['kiwi_name_pref'] = 'full'
            else:
                return False
            comment.email = kiwi['email']
            comment.kiwi_verified = True
    return True

if getattr(settings, 'KIWI_API_CODE', False):
    comment_will_be_posted.connect(kiwi_verification)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
