import re

# From http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()
def get_current_user():
    return getattr(_thread_locals, 'user', None)

class ThreadLocals(object):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)

ENTITY_MAP = None
def get_entity_map():
    global ENTITY_MAP
    if not ENTITY_MAP:
        import html_entities
        ENTITY_MAP = dict(html_entities.entities)
    return ENTITY_MAP

# See http://html5doctor.com/how-to-get-html5-working-in-ie-and-firefox-2/
class Firefox2HTML5Workaround(object):
    firefox1_9_re = re.compile(
        r'rv:(?:0|1\.(?:[1-8]|9pre|9a|9b[0-4])(?:\.[0-9.]+|\)))')
    entity_re = re.compile(r'&(?!quot|amp|lt|gt)([a-zA-Z]+);')
    def process_request(self, request):
        ua = request.META.get('HTTP_USER_AGENT')
        old_firefox = 'Gecko' in ua and self.firefox1_9_re.search(ua)
        request.using_xhtml = (old_firefox or 'xhtml' in request.GET)

    def process_response(self, request, response):
        if getattr(request, 'using_xhtml', False):
            response['Content-Type'] = 'application/xhtml+xml'
            response['X-Your-Browser'] = 'needs an upgrade'
            map = get_entity_map()
            def repl(match):
                num = map.get(match.group(1))
                return ('&#%d;' % num) if num else '?'
            response.content = self.entity_re.sub(repl, response.content)
        return response

class SetRemoteAddrFromForwardedFor(object):
      """
      Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
      latter is set. This is useful if you're sitting behind a reverse proxy that
      causes each request's REMOTE_ADDR to be set to 127.0.0.1.
  
      Note that this does NOT validate HTTP_X_FORWARDED_FOR. If you're not behind
      a reverse proxy that sets HTTP_X_FORWARDED_FOR automatically, do not use
      this middleware. Anybody can spoof the value of HTTP_X_FORWARDED_FOR, and
      because this sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, that means
      anybody can "fake" their IP address. Only use this when you can absolutely
      trust the value of HTTP_X_FORWARDED_FOR.
      """
      def process_request(self, request):
          try:
              real_ip = request.META['HTTP_X_FORWARDED_FOR']
          except KeyError:
              return None
          else:
              # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs. The
              # client's IP will be the first one.
              real_ip = real_ip.split(",")[0].strip()
              request.META['REMOTE_ADDR'] = real_ip

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
