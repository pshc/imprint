from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models
from datetime import datetime

class VolumeManager(CurrentSiteManager):
    def latest(self):
        return super(VolumeManager, self).all()[0]

class Volume(models.Model):
    """Represents a whole year's worth of issues."""
    on_site = VolumeManager()

    number = models.PositiveSmallIntegerField(db_index=True)
    site = models.ForeignKey(Site, related_name='volumes',
            default=Site.objects.get_current)

    class Meta:
        ordering = ['-number']
    def __unicode__(self):
        return u"Volume %d" % (self.number,)

class IssueManager(models.Manager):
    def latest(self):
        try:
            return Volume.on_site.latest().issues.all()[0]
        except IndexError:
            raise Issue.DoesNotExist

def next_issue_number():
    try:
        return Issue.objects.latest().number + 1
    except Issue.DoesNotExist:
        return 1

class Issue(models.Model):
    """One newspaper issue."""
    objects = IssueManager()

    volume = models.ForeignKey(Volume, related_name='issues',
            default=Volume.on_site.latest)
    number = models.PositiveSmallIntegerField(db_index=True,
            default=next_issue_number)
    date = models.DateField(db_index=True)

    class Meta:
        ordering = ['-volume', '-number']
        unique_together = (('volume', 'number'), ('volume', 'date'))
    def __unicode__(self):
        return u"Issue %s of %s" % (self.number, self.volume)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
