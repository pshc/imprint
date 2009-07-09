from django.contrib.syndication.feeds import Feed
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from issues.models import Issue
import datetime

class LatestPieces(Feed):
    title = Site.objects.get_current().name
    description = "News from the latest issue of " + \
            Site.objects.get_current().name
    ttl = "86400" # One day

    def link(self):
        return reverse('latest-issue')

    def items(self):
        return Issue.objects.latest_issue().pieces.filter(is_live=True)

    def item_pubdate(self, item):
        return datetime.datetime.combine(item.issue.date, datetime.time())

    def item_categories(self, item):
        return (unicode(item.section),)

    def item_extra_kwargs(self, item):
        return {'comments': item.get_absolute_url() + '#comments'}

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
