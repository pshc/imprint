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
            help_text="Determines the article's URL.")
    deck = models.CharField(max_length=200, blank=True,
            help_text="Optional subheadline.")
    section = models.ForeignKey(Section, related_name='articles')
    issue = models.ForeignKey(Issue, related_name='pieces',
            default=latest_issue_or(lambda i: i))
    is_live = models.BooleanField(u'Live?', default=True,
            help_text='Public visibility.')

    @property
    def authors(self):
        authors = set()
        for part in self.parts.select_related(): # Inefficient!
            authors += part.author_names
        return u", ".join(authors)

    class Meta:
        unique_together = [('issue', 'headline'), ('issue', 'slug')]

    def __unicode__(self):
        return unescape(strip_tags(self.headline))

    @models.permalink
    def get_absolute_url(self):
        date = self.issue.date
        return ('content.views.piece_detail', (), {
            'y': date.year, 'm': date.month, 'd': date.day,
            'section': self.section.slug, 'slug': self.slug})

class Part(models.Model):
    order = models.PositiveSmallIntegerField(db_index=True)
    piece = models.ForeignKey(Piece, related_name='parts')

    class Meta:
        ordering = ['order']

class Text(Part):
    title = models.CharField(max_length=100, blank=True,
            help_text='Optional title for this section of text')
    copy = models.XMLField()
    authors = models.ManyToManyField(Contributor, related_name='articles',
            through='Author')
    sources = models.CharField(max_length=200, blank=True,
            help_text='Appears as "With files from ..."')

    def __unicode__(self):
        if self.title:
            return self.title[:80]
        return unescape(strip_tags(self.copy))[:80]

    @property
    def author_names(self):
        return self.authors.values_list('name', flat=True)

class Author(models.Model):
    """Represents credit for some text content."""
    contributor = models.ForeignKey(Contributor)
    text = models.ForeignKey(Text)
    # TODO: Obtain default w/ AJAX
    position = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.contributor, self.position)

class Letter(Part):
    text = models.XMLField()
    author = models.CharField(max_length=50)
    program = models.CharField(max_length=50, blank=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    responding_to = generic.GenericForeignKey()

    def __unicode__(self):
        return u'Letter by %s' % (self.author,)

    @models.permalink
    def get_absolute_url(self):
        d = self.issue.date
        return ('content.views.article_detail', [d.year, d.month, d.day,
                self.section.slug, self.slug])

    @property
    def author_names(self):
        return self.author and [self.author] or []

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
