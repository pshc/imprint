from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models

class IssueManager(CurrentSiteManager):
    def latest_issue(self):
        try:
            return super(IssueManager, self).all()[0]
        except IndexError:
            raise Issue.DoesNotExist

def next_issue_number():
    try:
        return Issue.objects.latest_issue().number + 1
    except Issue.DoesNotExist:
        return 1

def next_volume_number():
    try:
        return Issue.objects.latest_issue().volume + 1
    except Issue.DoesNotExist:
        return 32

class Issue(models.Model):
    """One newspaper issue."""
    objects = IssueManager()

    date = models.DateField(db_index=True)
    number = models.PositiveSmallIntegerField(db_index=True,
            default=next_issue_number)
    volume = models.PositiveSmallIntegerField(db_index=True,
            default=next_volume_number)
    site = models.ForeignKey(Site, related_name='issues',
            default=Site.objects.get_current)

    class Meta:
        ordering = ['-volume', '-number']
        unique_together = (('volume', 'number'), ('volume', 'date'))
    def __unicode__(self):
        return u"Issue %s of volume %s" % (self.number, self.volume)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
