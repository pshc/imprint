from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.cache import cache
from django.db import models
from django.utils.html import strip_tags
from django.utils.http import urlquote
from issues.models import Issue, Section, Series, latest_issue_or, filter_live
import os
from people.models import Contributor
from utils import unescape, cache_with_key, date_tuple

def piece_cache_key(_, issue, section, slug):
    return 'piece/issue%d/%s/%s' % (issue.id, section, slug)

class PieceManager(models.Manager):
    @cache_with_key(piece_cache_key)
    def get_by_issue_section_slug(self, issue, section, slug):
        piece = self.get(issue=issue, section__slug=section, slug=slug,
                **filter_live())
        dummy = piece.units
        return piece

def delete_cached_piece(sender, instance=None, **kwargs):
    if issubclass(sender, Byline):
        instance = instance.copy
    elif issubclass(sender, Artist):
        instance = instance.image
    if isinstance(instance, Unit):
        instance = instance.piece
    assert isinstance(instance, Piece)
    key = piece_cache_key(None, instance.issue, instance.section.slug,
            instance.slug)
    cache.delete(key)

class Piece(models.Model):
    """Block of content in the paper. Holds text and media."""
    objects = PieceManager()
    headline = models.CharField(max_length=100,
            help_text="Markup is OK.")
    slug = models.SlugField(max_length=100, db_index=True,
            help_text="Determines the piece's URL.")
    deck = models.CharField(max_length=200, blank=True,
            help_text="Optional subheadline.")
    section = models.ForeignKey(Section, related_name='pieces')
    issue = models.ForeignKey(Issue, related_name='pieces',
            default=latest_issue_or(lambda i: i))
    series = models.ForeignKey(Series, related_name='pieces', null=True,
            blank=True, help_text="For example, a weekly column or comic.")
    is_live = models.BooleanField(u'Live', default=True,
            help_text='Public visibility.')
    is_featured = models.BooleanField(u'Feature', default=True,
            help_text='Should this appear in the cover preview?')
    order = models.PositiveSmallIntegerField(db_index=True, null=True,
            blank=True)
    redirect_to = models.CharField(max_length=100, blank=True,
            help_text='If set, redirects to the given URL instead of '
                      'displaying the article.')
    # Denormalized:
    contributors = models.ManyToManyField(Contributor, related_name='pieces',
            editable=False)

    class Meta:
        unique_together = [('issue', 'slug')]
        ordering = ('-order', 'id')

    def __unicode__(self):
        return unescape(strip_tags(self.headline))

    @models.permalink
    def get_absolute_url(self):
        y, m, d = date_tuple(self.issue.date)
        return ('piece-detail', (), {'y': y, 'm': m, 'd': d,
            'section': self.section.slug, 'slug': self.slug})

    @property
    def units(self):
        if not hasattr(self, '_units'):
            self._units = list(self.unit_set.all())
            for unit in self._units:
                if unit.type is Copy:
                    dummy = list(unit.copy.bylines)
                elif unit.type is Image:
                    dummy = list(unit.image.credits)
        return self._units

    @property
    def preview(self):
        if not self.units:
            return []
        first = self.units[0]
        if first.type is Image:
            first.image.prominence = 'all'
            if len(self.units) != 1:
                second = self.units[1]
                if second.type is Copy:
                    first.image.prominence = 'featured'
                    return [first, second]
                for unit in self.units[2:]:
                    if unit.type is Copy:
                        first.image.read_more = True
                        break
                else:
                    first.image.see_more = True
        return [first]

class Unit(models.Model):
    """One unit of content, part of a piece."""
    order = models.PositiveSmallIntegerField(db_index=True)
    piece = models.ForeignKey(Piece, related_name='unit_set')
    prominence = None
    see_more = False
    read_more = False

    def __unicode__(self):
        return u"#%d" % self.order

    class Meta:
        ordering = ['order']

    @property
    def type(self):
        if not hasattr(self, '_type'):
            # Poor man's downcast
            try:
                self._type = type(self.copy)
            except Copy.DoesNotExist:
                pass
            try:
                self._type = type(self.image)
            except Image.DoesNotExist:
                pass
        return self._type

    is_image = property(lambda s: s.type is Image)
    is_copy = property(lambda s: s.type is Copy)

class Copy(Unit):
    title = models.CharField(max_length=200, blank=True,
            help_text='Optional title for this section of text')
    body = models.XMLField()
    writers = models.ManyToManyField(Contributor, through='Byline')
    sources = models.CharField(max_length=200, blank=True,
            help_text='Appears as "With files from ..."')

    # Is this a response to a previous piece?
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    concerning = generic.GenericForeignKey()

    def __unicode__(self):
        if self.title:
            return self.title[:80]
        return unescape(strip_tags(self.body))[:80]

    @property
    def bylines(self):
        if not hasattr(self, '_bylines'):
            self._bylines = list(Byline.objects.filter(copy=self)
                    .select_related('contributor'))
        return self._bylines

    PREVIEW_MIN_LENGTH = 100
    @property
    def preview(self):
        """Return a few paragraphs of the copy. No terminating </p>."""
        copy = []
        length = 0
        paras = self.body.split('</p>')[:-1]
        while paras and length < self.PREVIEW_MIN_LENGTH:
            p = paras.pop(0)
            copy.append(p)
            length += len(p)
        return '</p>'.join(copy)

    @models.permalink
    def get_absolute_url(self):
        y, m, d = date_tuple(self.issue.date)
        return ('piece-detail', [y, m, d, self.section.slug, self.slug])

class Byline(models.Model):
    """Represents credit for some text content."""
    contributor = models.ForeignKey(Contributor)
    copy = models.ForeignKey(Copy)
    position = models.CharField(max_length=50, blank=True)
    is_after_copy = models.BooleanField(default=True)

    def __unicode__(self):
        if self.position:
            return u"%s (%s)" % (unicode(self.contributor), self.position)
        else:
            return unicode(self.contributor)

def get_image_filename(instance, filename):
    return instance.piece.issue.get_subdir_filename(filename)

class Image(Unit):
    image = models.ImageField(upload_to=get_image_filename)
    cutline = models.XMLField(blank=True)
    artists = models.ManyToManyField(Contributor, through='Artist')
    courtesy = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        return self.image.name

    @property
    def credits(self):
        if not hasattr(self, '_credits'):
            self._credits = list(Artist.objects.filter(image=self)
                    .select_related('contributor'))
        return self._credits

    @models.permalink
    def get_absolute_url(self):
        piece = self.piece
        y, m, d = date_tuple(piece.issue.date)
        return ('image-detail', (), {'y': y, 'm': m, 'd': d,
            'section': piece.section.slug, 'slug': piece.slug,
            'image': urlquote(os.path.basename(self.image.name))})

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

def propagate_liveness(sender, instance=None, **kwargs):
    """If an issue's liveness changes, set all its content's liveness too."""
    live = instance.is_live
    # So much for bulk UPDATE
    for piece in instance.pieces.filter(is_live=not live):
        piece.is_live = live
        piece.save()

models.signals.post_save.connect(propagate_liveness, sender=Issue)

for m in [Piece, Unit, Copy, Image, Byline, Artist]:
    models.signals.pre_save.connect(delete_cached_piece, sender=m)
    models.signals.pre_delete.connect(delete_cached_piece, sender=m)
del m

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
