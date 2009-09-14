import datetime
from django.conf import settings
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models
from django.utils import dates
from people.models import Contributor
import os
from utils import cache_with_key, date_tuple
# XXX: Move this to views:
from django.shortcuts import get_object_or_404
from django.http import Http404

HIGHLIGHT_COUNT = 4

class Series(models.Model):
    """A recurring column, comic, feature, etc."""
    name = models.CharField(max_length=50, db_index=True)
    slug = models.SlugField(max_length=50, db_index=True, unique=True,
            help_text="Determines what the name will look like in a URL.")
    contributors = models.ManyToManyField(Contributor, related_name='series',
            blank=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('area-detail', (), {'slug': self.slug})

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'series'

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
        return ('area-detail', (), {'slug': self.slug})

    class Meta:
        ordering = ('name',)

    @property
    def highlights(self):
        return self.pieces.all()[:HIGHLIGHT_COUNT]

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

    class Meta:
        ordering = ('section', 'assistant')

class IssueManager(CurrentSiteManager):
    def latest_issue(self):
        global CACHED_LATEST_ISSUE
        if not CACHED_LATEST_ISSUE:
            try:
                CACHED_LATEST_ISSUE = super(IssueManager, self).filter(
                        is_live=True)[0]
                dummy = CACHED_LATEST_ISSUE.previous
            except IndexError:
                raise self.model.DoesNotExist
        return CACHED_LATEST_ISSUE

    @cache_with_key(lambda s,y,m,d: 'site%d/issue/%d/%s/%d' % (
            Site.objects.get_current().id, int(y), m, int(d)))
    def get_by_date(self, y, m, d):
        try:
            date = datetime.date(int(y), dates.MONTHS_3_REV[m], int(d))
        except:
            # XXX: Views? In MY models?
            raise Http404
        issue = get_object_or_404(self.model, date__exact=date, is_live=True,
                site=Site.objects.get_current())
        dummy = issue.previous; dummy = issue.next
        return issue

def latest_issue_or(f, default=None):
    """Returns a function that applies `f` to the latest issue if there is one,
    or the default otherwise."""
    def deferred():
        try:
            return f(Issue.objects.latest_issue())
        except Issue.DoesNotExist:
            return default
    return deferred

def get_issue_dir(instance, filename):
    return instance.get_subdir_filename(filename)

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
            through='IssueSection')
    thumbnail = models.ImageField(blank=True, null=True,
            upload_to=lambda i, f: i.get_subdir_filename(f))

    class Meta:
        ordering = ['-volume', '-number']
        unique_together = (('volume', 'number'), ('volume', 'date'))

    def __unicode__(self):
        return u"Issue %s of volume %s" % (self.number, self.volume)

    @models.permalink
    def get_absolute_url(self):
        y, m, d = date_tuple(self.date)
        return ('issue-detail', date_tuple(self.date))

    def save(self, **kwargs):
        make_sections = not self.id
        super(Issue, self).save(**kwargs)
        # Copy over navigation from the previous issue
        if make_sections:
            def copy_previous_sections(issue):
                for i,s in enumerate(IssueSection.objects.filter(issue=issue)):
                    IssueSection.objects.create(issue=self, section=s.section,
                            alt_section_name=s.alt_section_name, order=i+1)
            latest_issue_or(copy_previous_sections, lambda: None)()
        try:
            os.makedirs(os.path.join(settings.MEDIA_ROOT, self.media_dir))
        except OSError, e:
            if e.errno != 17:
                raise

    @property
    def media_dir(self):
        return os.path.join(settings.SITE_MEDIA_SUBDIR,
                'vol%02d' % self.volume, 'issue%02d' % self.number)

    def get_subdir_filename(self, filename):
        dir = self.media_dir
        while True:
            fnm = os.path.join(dir, filename)
            if not os.path.exists(os.path.join(settings.MEDIA_ROOT, fnm)):
                return fnm
            # File with this name already exists...
            base, ext = os.path.splitext(filename)
            filename = base + '_' + ext

    @property
    def previous(self):
        if not hasattr(self, '_previous'):
            try:
                self._previous = self.get_previous_by_date(is_live=True)
            except Issue.DoesNotExist:
                self._previous = None
        return self._previous

    @property
    def next(self):
        if not hasattr(self, '_next'):
            try:
                self._next = self.get_next_by_date(is_live=True)
            except Issue.DoesNotExist:
                self._next = None
        return self._next

    @property
    def nav_sections(self):
        return IssueSection.objects.select_related().filter(issue=self)

    @property
    def highlights(self):
        return self.pieces.order_by('-is_featured', 'order')[:HIGHLIGHT_COUNT]

class IssueSection(models.Model):
    """Stores info about the order and naming of section navigation links."""
    issue = models.ForeignKey(Issue)
    section = models.ForeignKey(Section)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
    alt_section_name = models.CharField('Title', max_length=50,
            blank=True, null=True,
            help_text='Optional alternate title in the navigation bar only.')

    @property
    def section_name(self):
        return self.alt_section_name or self.section.name

    def __unicode__(self):
        return self.section_name

    class Meta:
        ordering = ('order', 'id')

# This is so commonly used, we'll just cache it right here
CACHED_LATEST_ISSUE = None
def clear_issue_cache(*args, **kwargs):
    global CACHED_LATEST_ISSUE
    CACHED_LATEST_ISSUE = None

# Keep it fresh
for m in [Issue, Section, Site]:
    models.signals.post_save.connect(clear_issue_cache, sender=m)
    models.signals.post_delete.connect(clear_issue_cache, sender=m)
del m

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
