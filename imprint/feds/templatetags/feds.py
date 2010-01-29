from django.core.cache import cache
from django.db.models import Count
from django.template import Library
from django.template.loader import render_to_string
from urllib import urlencode
import datetime

register = Library()

@register.simple_tag
def google_pie_chart(position):
    """Renders a pie chart with the overall results for the given poll."""
    counts = position.candidates.annotate(Count('votes')).values(
            'name', 'votes__count', 'graph_colour')
    labels = ('%s (%d)' % (v['name'], v['votes__count']) for v in counts)
    options = {'cht': 'p', 'chs': '600x300',
            'chtt': position.name,
            'chl': '|'.join(labels),
            'chd': 't:' + ','.join(str(v['votes__count']) for v in counts),
            'chco': ','.join(v['graph_colour'] for v in counts),
            'chp': '5.5', # angle in radians
            }
    image_url = "http://chart.apis.google.com/chart?" + urlencode(options)
    return render_to_string('feds/google_chart.html', locals())

@register.simple_tag
def google_daily_line_graph(position):
    """Renders a line chart with by-day vote counts for the given poll."""
    html = cache.get('feds-%s-results' % position.slug)
    if html:
        return html
    from imprint.feds.models import Vote
    candidates = position.candidates
    # XXX: Terrible temporary hack
    data = dict((c.id, []) for c in candidates.all())
    last_month = None
    today = datetime.date.today().timetuple()[:3]
    labels = []
    max_day_count = 1 
    for day in Vote.objects.dates('voted_on', 'day'):
        if day.timetuple()[:3] == today:
            continue # Don't show in-progress results
        if last_month != day.month: # New month?
            last_month = day.month
            labels.append(day.strftime('%b %e'))
        else:
            labels.append(day.strftime('%e'))
        rng = (day, day + datetime.timedelta(days=1))
        for candidate in candidates.all():
            day_count = Vote.objects.filter(candidate=candidate,
                    voted_on__range=rng).count()
            data[candidate.id].append(str(day_count))
            max_day_count = max(max_day_count, day_count)
        """
        day_counts = candidates.annotate(Count('votes')).filter(
                votes__voted_on__range=rng).values_list('id', 'votes__count')
        for slug, day_count in day_counts:
            data[id].append(str(day_count))
        """
    datasets = []
    colours = []
    names = []
    for candidate in candidates.all():
        datasets.append(','.join(data[candidate.id]))
        colours.append(candidate.graph_colour)
        names.append(candidate.name)
    options = {'cht': 'lc', 'chs': '740x300',
            'chtt': position.name,
            'chd': 't:' + '|'.join(datasets),
            'chds': '0,%d' % max_day_count,
            'chdl': '|'.join(names),
            'chco': ','.join(colours),
            'chxt': 'x,y,r',
            'chxl': '0:|%s|1:||%d|2:||%d' % ('|'.join(labels),
                    max_day_count, max_day_count),
            }
    image_url = "http://chart.apis.google.com/chart?" + urlencode(options)
    html = render_to_string('feds/google_chart.html', locals())
    cache.set('feds-%s-results' % position.slug, html)
    return html

@register.simple_tag
def twitter_status(twitter_username):
    status = cache.get('feds-%s-status' % twitter_username)
    if status is None:
        try:
            import twitter
            user = twitter.Api().GetUser(twitter_username)
            status = user.status
            status = render_to_string('feds/twitter_status.html', locals())
        except:
            status = ''
        cache.set('feds-%s-status' % twitter_username, status)
    return status

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
