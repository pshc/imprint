from django import template
from django.conf import settings
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from imprint.utils import unescape
import re

register = template.Library()

@register.simple_tag
def googleanalytics():
    key = getattr(settings, 'GOOGLE_ANALYTICS_KEY', None)
    if not key:
        return ''
    return mark_safe("""<!-- Google Analytics -->
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
try {
var pageTracker = _gat._getTracker("API_KEY");
pageTracker._trackPageview();
} catch(err) {}</script>""".replace('API_KEY', key))

def do_url_sub(match):
    # paranoia
    url = match.group(0).replace('"', '').replace('<', '').replace('>', '')
    text = url if len(url) <= 80 else url[:77] + u'...'
    return u'<a href="%s" rel="nofollow" >%s</a>' % (url, text)

url_re = re.compile(r'''https?://[a-zA-Z0-9/.\-_+~#=?%&;,:\[\]{}`!$^*()]+'''
    r'''[a-zA-Z0-9#?/\-_+=)]''')
@register.filter
def clickablelinks(text):
    text = conditional_escape(text)
    return mark_safe(url_re.sub(do_url_sub, text))

html_tag_re = re.compile(r'(<[^<]*>)')
break_re = re.compile(r'([^ ]{100})')
@register.filter
def breaklongwords(text):
    pieces = [p if p.startswith(u'<')
              else escape(break_re.sub(u'\\1 ', unescape(p)))
              for p in html_tag_re.split(text)]
    return mark_safe(u''.join(pieces))

# For debugging
@register.filter
def togglesqlfields(stmt):
    m = re.match("^SELECT(.+?)FROM(.+)$", stmt)
    if not m:
        return stmt
    return mark_safe('''SELECT <span style="cursor: pointer" onclick="
    $(this).hide(); $(this).next('span').show();
    ">...</span><span style="display: none;">%s</span> FROM %s'''
        % tuple(map(conditional_escape, m.groups())))


@register.tag
def lookup(parser, token):
    """Uses template variables to perform a dict lookup and name the result."""
    in_ = as_ = None
    try:
        tag_name, key, in_, d, as_, name = token.split_contents()
    except ValueError:
        pass
    if in_ != 'in' or as_ != 'as':
        raise template.TemplateSyntaxError, ("lookup syntax: {% lookup "
                "<key> in <dict> as <bound name> %}...{% endlookup %}")
    nodelist = parser.parse(('endlookup',))
    parser.delete_first_token()
    return LookupNode(key, d, name, nodelist)

class LookupNode(template.Node):
    def __init__(self, key, d, name, nodelist):
        self.key = template.Variable(key)
        self.d = template.Variable(d)
        self.name = name
        self.nodelist = nodelist

    def __repr__(self):
        return '<LookupNode>'

    def render(self, context):
        d = self.d.resolve(context)
        try:
            key = self.key.resolve(context)
            v = d.get(key, '')
        except template.VariableDoesNotExist:
            v = ''
        context.push()
        context[self.name] = v
        html = self.nodelist.render(context)
        context.pop()
        return html

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
