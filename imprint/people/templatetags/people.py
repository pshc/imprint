from django.template import Library, Node
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = Library()

@register.simple_tag
def contributor_link(c):
    """Renders a contributor with a link to their profile."""
    return mark_safe('<a href="%s">%s</a>'
            % (c.get_absolute_url(), conditional_escape(c.name)))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
