from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from issues.models import *
import datetime

_cur_site = Site.objects.get_current()

class PieceFeed(Feed):
    ttl = "9001"

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def items(self, obj):
        return obj.pieces.filter(is_live=True).order_by('issue__date',
                'order')[:20]

    def item_pubdate(self, item):
        return datetime.datetime.combine(item.issue.date, datetime.time())

    def item_extra_kwargs(self, item):
        return {'comments': item.get_absolute_url() + '#comments'}

class LatestPieces(PieceFeed):
    title = _cur_site.name
    description = "News from the latest issue of " + _cur_site.name

    def link(self):
        return reverse('latest-issue')

    def items(self):
        return Issue.objects.latest_issue().pieces.filter(is_live=True)

    def item_categories(self, item):
        return (unicode(item.section),)

class LatestSectionPieces(PieceFeed):
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Section.objects.get(slug=bits[0])

    def title(self, obj):
        return u'%s from %s' % (obj.name, _cur_site.name)

    def description(self, obj):
        return u"Recent articles from the %s section" % (obj.name,)

class LatestSeriesPieces(PieceFeed):
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Series.objects.get(slug=bits[0])

    def title(self, obj):
        return u'%s from %s' % (obj.name, _cur_site.name)

    def description(self, obj):
        return u"Recent articles from %s" % (obj.name,)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
