import datetime
from django.conf import settings
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db.models.signals import post_save, post_delete
from django.db import models
from django.shortcuts import get_object_or_404
from people.models import Contributor
import os
from utils import cache_with_key

class Section(models.Model):
    """One section of the newspaper."""
    name = models.CharField(max_length=50, db_index=True)
    slug = models.SlugField(max_length=50, db_index=True,
            help_text="Determines what the name will look like in a URL.")
    editors = models.ManyToManyField(Contributor, through='SectionEditorship',
            related_name='sections')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('section-latest-issue', (), {'slug': self.slug})

    class Meta:
        ordering = ('name',)

class SectionEditorship(models.Model):
    """Represents one (co/assistant/etc.) editorship position."""
    contributor = models.ForeignKey(Contributor)
    section = models.ForeignKey(Section)
    assistant = models.BooleanField(default=False)
    co = models.BooleanField(u"Co-?", default=False,
            help_text=u'Adds a "co-" prefix to the editorial title')

    @property
    def title(self):
        prefix = u"Co-" if self.co else u""
        if self.assistant: prefix += u"Assistant "
        return u"%s%s Editor" % (prefix, self.section.name)

    def __unicode__(self):
        return "%s, %s" % (self.contributor, self.title)

class IssueManager(CurrentSiteManager):
    def latest_issue(self):
        global CACHED_LATEST_ISSUE
        if CACHED_LATEST_ISSUE:
            return CACHED_LATEST_ISSUE
        try:
            CACHED_LATEST_ISSUE = super(IssueManager, self).filter(
                    is_live=True)[0]
            return CACHED_LATEST_ISSUE
        except IndexError:
            raise self.model.DoesNotExist

    @cache_with_key(lambda s,y,m,d: 'site%d/issue/%d/%d/%d' % (
            Site.objects.get_current().id, int(y), int(m), int(d)))
    def get_by_date(self, y, m, d):
        date = datetime.date(int(y), int(m), int(d))
        return get_object_or_404(self.model, date__exact=date, is_live=True,
                site=Site.objects.get_current())

def latest_issue_or(f, default=None):
    """Returns a function that applies `f` to the latest issue if there is one,
    or the default otherwise."""
    def deferred():
        try:
            return f(Issue.objects.latest_issue())
        except Issue.DoesNotExist:
            return default
    return deferred

def get_previous_sections():
    return latest_issue_or(lambda i: i.sections.values_list('id', flat=True))

class Issue(models.Model):
    """One newspaper issue."""
    objects = IssueManager()

    date = models.DateField(db_index=True)
    number = models.PositiveSmallIntegerField(db_index=True,
            default=latest_issue_or(lambda i: i.number + 1, 1))
    volume = models.PositiveSmallIntegerField(db_index=True,
            default=latest_issue_or(lambda i: i.volume, 32))
    is_live = models.BooleanField('Live', default=False)
    site = models.ForeignKey(Site, related_name='issues',
            default=Site.objects.get_current)
    sections = models.ManyToManyField(Section, related_name='issues',
            default=get_previous_sections, blank=True,
            help_text="Controls which sections appear in the header banner "
                      + " for this issue.")

    class Meta:
        ordering = ['-volume', '-number']
        unique_together = (('volume', 'number'), ('volume', 'date'))

    def __unicode__(self):
        return u"Issue %s of volume %s" % (self.number, self.volume)

    @models.permalink
    def get_absolute_url(self):
        return ('issue-detail', self.date.timetuple()[:3])

    @property
    def media_dir(self):
        dir = os.path.join(self.site.domain, 'vol%02d' % self.volume,
                'issue%02d' % self.number)
        try:
            os.makedirs(os.path.join(settings.MEDIA_ROOT, dir))
        except OSError, e:
            if e.errno != 17:
                raise
        return dir

    def get_subdir_filename(self, filename):
        dir = self.media_dir
        while True:
            fnm = os.path.join(dir, filename)
            if not os.path.exists(os.path.join(settings.MEDIA_ROOT, fnm)):
                return fnm
            # File with this name already exists...
            base, ext = os.path.splitext(filename)
            filename = base + '_' + ext

# This is so commonly used, we'll just cache it right here
CACHED_LATEST_ISSUE = None
def clear_issue_cache(*args, **kwargs):
    CACHED_LATEST_ISSUE = None

# Keep it fresh
for m in [Issue, Section, Site]:
    post_save.connect(clear_issue_cache, sender=m)
    post_delete.connect(clear_issue_cache, sender=m)
del m

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
