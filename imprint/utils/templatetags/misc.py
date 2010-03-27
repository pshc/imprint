from django.conf import settings
from django.template import Library
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe, SafeData
import re

register = Library()

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

space_re = re.compile(r'\s')
def starts_with_whitespace(text):
    return space_re.match(text)

entity_re = re.compile(r'(&[^;]*;|\s+)')
def split_html(html):
    while True:
        split = entity_re.split(html, 1)
        if len(split) == 1:
            if split[0]:
                yield split[0]
            raise StopIteration
        text, interest, html = split
        if text:
            yield text
        yield interest

def take_html(count, html, suffix=''):
    results = []
    for frag in split_html(html):
        entity = frag.startswith('&') and frag
        frag_len = 1 if entity else len(frag)
        count -= frag_len
        if count < 0:
            results.append(entity or frag[:count + frag_len])
            if suffix:
                results.append(suffix)
            break
        results.append(frag)
    return u''.join(results)

def tag_url(url):
    # Trying to remove "s etc. here is futile; there are many avenues of attack
    # here that don't require them. Whitelisting, proper encoding are the way.
    # assert '"' not in text - THBBBT!
    text = url if len(url) <= 80 else take_html(80, url, '&hellip;')
    return u'<a href="%s" rel="nofollow" >%s</a>' % (url, text)

def pop_trailing_entities(html):
    html = list(split_html(html))
    after = []
    while html[-1].startswith('&'):
        after.append(html.pop())
    return u''.join(html), u''.join(after)

def recede_url(url):
    cutoff = len(url)
    parens = url.count('(') - url.count(')')
    while parens < 0:
        if cutoff < 1:
            cutoff = len(url)
            break
        c = url[cutoff-1]
        if c == '(': parens -= 1
        elif c == ')': parens += 1
        cutoff -= 1
    return url[:cutoff], url[cutoff:]

html_tag_re = re.compile(r'(<[^<]*>)')
def apply_to_content(f, text):
    return u''.join(p if p.startswith(u'<') else f(p)
                    for p in html_tag_re.split(conditional_escape(text)))

url_re = re.compile(r'''((?:https?://|www\.)'''
        r'''[a-zA-Z0-9/.\-_+~#=?%&;,:\[\]{}`!$^*()]+[a-zA-Z0-9#?/\-_+=);])''')
def make_clickable(text):
    remaining = text
    result = []
    while True:
        split = url_re.split(remaining, 1)
        if len(split) == 1:
            result.append(split[0])
            break
        before, url, after = split
        result.append(before)
        if url.startswith('www.'):
            url = 'http://' + url
        assert url.startswith('http')
        url, end = pop_trailing_entities(url)
        url, cut = recede_url(url)
        result.append(tag_url(url))
        remaining = u'%s%s%s' % (cut, end, after) if cut or end else after
    return u''.join(result)

@register.filter
def clickablelinks(html):
    return mark_safe(apply_to_content(make_clickable, html))

BREAK_LEN = 50

def break_up_long_words(text):
    if len(text) <= BREAK_LEN:
        return text
    result = []
    chars_left = BREAK_LEN
    for frag in split_html(text):
        if starts_with_whitespace(frag):
            if result and result[-1] == '&shy':
                result.pop()
            result.append(frag)
            chars_left = BREAK_LEN
            continue
        entity = frag.startswith('&') and frag
        chars_left -= 1 if entity else len(frag)
        while chars_left < 0:
            chars_left += BREAK_LEN
            pos = BREAK_LEN if chars_left <= 0 else BREAK_LEN - chars_left
            result.append(entity or frag[:pos])
            result.append(u'&shy;')
            frag = '' if entity else frag[pos:]
        if frag:
            result.append(frag)
    return u''.join(result)

@register.filter
def breaklongwords(text):
    return mark_safe(apply_to_content(break_up_long_words, text))

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

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
