from django.contrib.auth.models import User
from django.db import models

class Contributor(models.Model):
    """Someone who has created content for the paper."""
    name = models.CharField(max_length=50, db_index=True)
    position = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    user = models.OneToOneField(User, blank=True, null=True)

    @property
    def slug(self):
        # If we ever have two people with the same name, this means trouble
        return self.name.replace(' ', '')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
