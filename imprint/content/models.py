from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.utils.html import strip_tags
from issues.models import Issue, Section, latest_issue_or
from people.models import Contributor
from utils import unescape

class Piece(models.Model):
    """Block of content in the paper. Holds text and images."""
    headline = models.CharField(max_length=100,
            help_text="Markup is OK.")
    slug = models.SlugField(max_length=100, db_index=True,
            help_text="Determines the piece's URL.")
    deck = models.CharField(max_length=200, blank=True,
            help_text="Optional subheadline.")
    section = models.ForeignKey(Section, related_name='pieces')
    issue = models.ForeignKey(Issue, related_name='pieces',
            default=latest_issue_or(lambda i: i))
    is_live = models.BooleanField(u'Live?', default=True,
            help_text='Public visibility.')

    @property
    def authors(self):
        authors = set()
        for part in self.parts.select_related(): # Inefficient!
            authors.update(part.author_names)
        return u", ".join(authors)

    class Meta:
        unique_together = [('issue', 'headline'), ('issue', 'slug')]
        ordering = ('-id',) # TODO: Manually specify order somehow...

    def __unicode__(self):
        return unescape(strip_tags(self.headline))

    @models.permalink
    def get_absolute_url(self):
        date = self.issue.date
        return ('content.views.piece_detail', (), {
            'y': date.year, 'm': date.month, 'd': date.day,
            'section': self.section.slug, 'slug': self.slug})

class Part(models.Model):
    """One unit of content, part of a piece."""
    order = models.PositiveSmallIntegerField(db_index=True)
    piece = models.ForeignKey(Piece, related_name='parts')

    def __unicode__(self):
        return u"#%d" % self.order

    class Meta:
        ordering = ['order']

class Text(Part):
    title = models.CharField(max_length=200, blank=True,
            help_text='Optional title for this section of text')
    copy = models.XMLField()
    writers = models.ManyToManyField(Contributor, through='Writer')
    sources = models.CharField(max_length=200, blank=True,
            help_text='Appears as "With files from ..."')

    # Is this a response to a previous piece?
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    concerning = generic.GenericForeignKey()

    def __unicode__(self):
        if self.title:
            return self.title[:80]
        return unescape(strip_tags(self.copy))[:80]

    @property
    def author_names(self):
        return self.authors.values_list('name', flat=True)

    @property
    def credits(self):
        return Writer.objects.filter(text=self)

    PREVIEW_MIN_LENGTH = 100
    @property
    def copy_preview(self):
        """Return a few paragraphs of the copy."""
        copy = []
        length = 0
        paras = self.copy.split('</p>')
        while length < self.PREVIEW_MIN_LENGTH:
            p = paras.pop(0)
            copy.append(p)
            length += len(p)
        url = ' <a href="%s" class="more">Read more...</a>' % (
                self.piece.get_absolute_url(),)
        copy[-1] = copy[-1] + url
        copy.append('')
        return '</p>'.join(copy)

    @models.permalink
    def get_absolute_url(self):
        d = self.issue.date
        return ('piece-detail', [d.year, d.month, d.day,
                self.section.slug, self.slug])

class Writer(models.Model):
    """Represents credit for some text content."""
    contributor = models.ForeignKey(Contributor)
    text = models.ForeignKey(Text)
    position = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        if self.position:
            return u"%s (%s)" % (unicode(self.contributor), self.position)
        else:
            return unicode(self.contributor)

def get_image_filename(instance, filename):
    return get_issue_subdir_filename(instance.piece.issue, filename)

class Image(Part):
    image = models.FileField(upload_to=get_image_filename)
    cutline = models.XMLField(blank=True)
    artists = models.ManyToManyField(Contributor, through='Artist')

    def __unicode__(self):
        return self.image.name

    @property
    def author_names(self):
        return self.artists.values_list('name', flat=True)
    
    @property
    def credits(self):
        return Artist.objects.filter(image=self)

PHOTOGRAPHER, GRAPHIC_ARTIST = 1, 2
ARTIST_TYPES = ((PHOTOGRAPHER, u'Photo by (name)'),
                (GRAPHIC_ARTIST, u'Graphic by (name)'))

class Artist(models.Model):
    image = models.ForeignKey(Image)
    contributor = models.ForeignKey(Contributor)
    type = models.PositiveSmallIntegerField(choices=ARTIST_TYPES, default=1)

    def __unicode__(self):
        return self.get_type_display().replace(u'(name)',
                unicode(self.contributor))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
