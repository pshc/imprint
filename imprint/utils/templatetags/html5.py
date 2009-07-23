from django.contrib.humanize.templatetags import humanize
from django.template import Library, defaultfilters
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = Library()

def time_tag(value, str):
    return mark_safe(u'<time datetime="%s">%s</time>' % (value.isoformat(),
        conditional_escape(str)))

@register.filter
def html5naturalday(value, arg=None):
    formatted = humanize.naturalday(value, arg)
    return time_tag(value, formatted)

@register.filter
def html5date(value, arg=None):
    formatted = defaultfilters.date(value, arg)
    return time_tag(value, formatted)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
