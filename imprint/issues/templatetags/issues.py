from django import template
from django.core.urlresolvers import reverse
from django.utils.html import conditional_escape
from utils import date_tuple

register = template.Library()

@register.tag
def section_link(parser, token):
    """Renders an issue-specific link if we're already being issue-specific,
    or else the top-level (latest-issue) /section-name/ link."""
    try:
        tag_name, section = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, \
            "%r tag requires a single argument" % token.contents.split()[0]
    return SectionLinkNode(section)

class SectionLinkNode(template.Node):
    def __init__(self, section):
        self.section = template.Variable(section)
    def render(self, context):
        try:
            section = self.section.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        if hasattr(section, 'section'):
            name = section.section_name # IssueSection
            section = section.section
        else:
            name = section.name
        if context.get('is_specific_issue', False):
            date = date_tuple(context['issue'].date)
            url = reverse('section-detail', args=date + (section.slug,))
        else:
            url = section.get_absolute_url()
        return '<a href="%s">%s</a>' % (url, conditional_escape(name))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
