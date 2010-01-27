from django.db.models import Count
from django.template import Context, Library
from django.template.loader import get_template

register = Library()

@register.simple_tag
def google_chart(position):
    """Renders a chart with the results for the given poll."""
    counts = position.candidates.annotate(Count('votes')).values(
            'name', 'votes__count', 'graph_colour')
    labels = ('%s (%d)' % (v['name'], v['votes__count']) for v in counts)
    options = {'cht': 'p', 'chs': '600x300',
            'chtt': position.name.replace(' ', '+'),
            'chl': '|'.join(labels),
            'chd': 't:' + ','.join(str(v['votes__count']) for v in counts),
            'chco': ','.join(v['graph_colour'] for v in counts),
            }
    options = '&'.join('%s=%s' % kv for kv in options.iteritems())
    image_url = "http://chart.apis.google.com/chart?" + options
    return get_template('feds/google_chart.html').render(Context(locals()))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
