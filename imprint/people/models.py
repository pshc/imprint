from django.contrib.auth.models import User
from django.db import models

def slugify_name(name):
    # Is this sufficient?
    return name.replace(' ', '').replace('.', '')

class Contributor(models.Model):
    """Someone who has created content for the paper."""
    # Names have to be unique for now. Middle names should suffice.
    name = models.CharField(max_length=50, db_index=True, unique=True)
    slug = models.CharField(max_length=50, db_index=True, unique=True,
            editable=False)
    position = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    user = models.OneToOneField(User, blank=True, null=True)

    @property
    def with_position(self):
        return '%s (%s)' % (self.name, self.position) if self.position \
                else self.name

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]

    @models.permalink
    def get_absolute_url(self):
        return ('contributor-detail', (), {'slug': self.slug})
    
    def save(self, *args, **kwargs):
        self.slug = slugify_name(self.name)
        super(Contributor, self).save(*args, **kwargs)

    def merge_with(self, people):
        #from content.models import Byline, Artist
        for p in people:
            assert p.id != self.id
            for a in p.byline_set.all():
                a.contributor = self
                a.save()
            for a in p.artist_set.all():
                a.contributor = self
                a.save()
            for piece in p.pieces.all():
                piece.contributors.remove(p)
                piece.contributors.add(self)
                piece.save()
            for series in p.series.all():
                series.contributors.remove(p)
                series.contributors.add(self)
            p.delete()


# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
