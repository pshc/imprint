import datetime
from django.conf import settings
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models
from django.utils import dates
from people.models import Contributor
from utils import cache_with_key, date_tuple, get_current_user, parse_ymd
import os

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

    def get_highlights(self, issue=None):
        qs = self.pieces.all()
        if issue:
            qs = qs.filter(issue=issue)
        return qs[:HIGHLIGHT_COUNT]

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

def filter_live():
    """Returns kwargs suitable for .filter(), for issue permissions"""
    user = get_current_user()
    return {} if user and user.is_staff else {'is_live': True}

class IssueManager(CurrentSiteManager):
    def latest_issue(self):
        user = get_current_user()
        # Staff can see non-live issues
        if user and user.is_staff:
            return self.all()[0]
        # Otherwise, only show live issues
        return self.filter(is_live=True)[0]

    @cache_with_key(lambda s,y,m,d: 'site%d/issue/%d/%s/%d' % (
            Site.objects.get_current().id, int(y), m, int(d)))
    def get_by_date(self, y, m, d):
        date = parse_ymd(y, m, d)
        if not date:
            raise Issue.DoesNotExist
        issue = self.get(date__exact=date, site=Site.objects.get_current(),
                **filter_live())
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
    is_live = models.BooleanField('Live on site', default=False,
            help_text='Enable this once all content is uploaded.')
    site = models.ForeignKey(Site, related_name='issues',
            default=Site.objects.get_current)
    sections = models.ManyToManyField(Section, related_name='issues',
            through='IssueSection')
    thumbnail = models.ImageField(blank=True, null=True,
            help_text='Should be 170 px wide.',
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
        make_sections = False
        if not self.id:
            try:
                prev = Issue.objects.latest_issue()
                make_sections = True
            except Issue.DoesNotExist:
                pass
        super(Issue, self).save(**kwargs)
        # Copy over navigation from the previous issue
        if make_sections:
            for i,s in enumerate(IssueSection.objects.filter(issue=prev)):
                IssueSection.objects.create(issue=self, section=s.section,
                        alt_section_name=s.alt_section_name, order=i+1)
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
                self._previous = self.get_previous_by_date(**filter_live())
            except Issue.DoesNotExist:
                self._previous = None
        return self._previous

    @property
    def next(self):
        if not hasattr(self, '_next'):
            try:
                self._next = self.get_next_by_date(**filter_live())
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

    def save(self, **kwargs):
        if not self.id and self.order is None:
            # Put this at the bottom
            try:
                self.order = IssueSection.objects.filter(issue=self.issue,
                        section=self.section).order_by('-order')[0].order + 1
            except IndexError:
                self.order = 1
        super(IssueSection, self).save(**kwargs)

    class Meta:
        ordering = ('order', 'id')

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
