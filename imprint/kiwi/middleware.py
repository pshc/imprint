from django.conf import settings

class KiwiNameFormatMiddleware():
    def process_request(self, request):
        if not getattr(settings, 'KIWI_API_CODE', False):
            return
        if request.method == 'POST' and 'kiwi_name_format' in request.POST:
            kiwi = request.session.get('kiwi_info', None)
            if kiwi:
                format = request.POST['kiwi_name_format']
                if format == 'firstlast':
                    request.session['kiwi_name_pref'] = 'firstlast'
                elif format == 'full':
                    request.session['kiwi_name_pref'] = 'full'
                elif format == 'middleinitials':
                    request.session['kiwi_name_pref'] = 'middleinitials'

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
