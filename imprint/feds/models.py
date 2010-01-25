from django.db import models
from datetime import datetime

class Position(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True,
            help_text="Determines the position's URL.")
    description = models.TextField(blank=True, help_text="HTML.")
    order = models.SmallIntegerField()

    def __unicode__(self):
        return self.name
    
    @property
    def acclaimed(self):
        return self.candidates.count() == 1

    class Meta:
        ordering = ['order', 'name']

class Candidate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True,
            help_text="Determines the candidate's URL.")
    position = models.ForeignKey(Position, related_name='candidates')
    description = models.TextField(blank=True, help_text="HTML.")
    image = models.ImageField(upload_to='images/feds', blank=True)
    website = models.URLField(blank=True)

    def __unicode__(self):
        return self.name
        
    class Meta:
        ordering = ['name']

class UserAgent(models.Model):
    agent = models.CharField(max_length=500, unique=True)

    def __unicode__(self):
        return self.agent

class VoteManager(models.Manager):
    def create(self, candidate, user_agent, voted_on=None, **kwargs):
        if isinstance(candidate, basestring):
            candidate = Candidate.objects.get(slug=candidate)
        if isinstance(user_agent, basestring):
            user_agent = UserAgent.objects.get_or_create(agent=user_agent)[0]
        if voted_on is None:
            voted_on = datetime.now()
        kwargs.update(locals())
        del kwargs['self'], kwargs['kwargs']
        return super(VoteManager, self).create(**kwargs)

class Vote(models.Model):
    candidate = models.ForeignKey(Candidate, related_name='votes')
    voted_on = models.DateTimeField(default=datetime.now, db_index=True)
    user_agent = models.ForeignKey(UserAgent, null=True)
    ip = models.IPAddressField(db_index=True)
    objects = VoteManager()

    class Meta:
        ordering = ['-voted_on', 'ip']

    def __unicode__(self):
        return u'Vote for %s on %s from %s' % (self.candidate, self.voted_on,
                self.ip)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
