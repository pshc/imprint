from django.conf import settings

def kiwi_info(request):
    """Provides kiwi_info as `kiwi` in the context"""
    enabled = getattr(settings, 'KIWI_API_CODE', False)
    if enabled:
        pref = request.session.get('kiwi_name_pref', 'firstlast')
        return {'kiwi': request.session.get('kiwi_info', ''),
                'kiwi_enabled': True, 'kiwi_name_pref': pref}
    else:
        return {'kiwi_enabled': False}

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
