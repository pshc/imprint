from django.conf import settings
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models
from people.models import Contributor
import os

class Section(models.Model):
    """One section of the newspaper."""
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, db_index=True,
            help_text="Determines what the name will look like in a URL.")
    editors = models.ManyToManyField(Contributor, through='SectionEditorship',
            related_name='sections')

    def __unicode__(self):
        return self.name

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
        try:
            return super(IssueManager, self).all()[0]
        except IndexError:
            raise Issue.DoesNotExist

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

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
