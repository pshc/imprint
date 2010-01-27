from django.db.models import Count
from django.template import Context, Library
from django.template.loader import get_template

register = Library()

@register.simple_tag
def google_chart(position):
    """Renders a chart with the results for the given poll."""
    vote_counts = position.candidates.annotate(Count('votes')).values_list(
            'name', 'votes__count')
    labels = []
    options = {'cht': 'p', 'chs': '600x300',
            'chtt': position.name.replace(' ', '+'),
            'chl': '|'.join('%s (%d)' % tuple(nc) for nc in vote_counts),
            'chd': 't:' + ','.join(str(count) for name, count in vote_counts),
            }
    options = '&'.join('%s=%s' % kv for kv in options.iteritems())
    image_url = "http://chart.apis.google.com/chart?" + options
    return get_template('feds/google_chart.html').render(Context(locals()))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
