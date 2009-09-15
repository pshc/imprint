import re

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
        if request.using_xhtml:
            response['Content-Type'] = 'application/xhtml+xml'
            response['X-Your-Browser'] = 'needs an upgrade'
            map = get_entity_map()
            def repl(match):
                num = map.get(match.group(1))
                return ('&#%d;' % num) if num else '?'
            response.content = self.entity_re.sub(repl, response.content)
        return response

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
