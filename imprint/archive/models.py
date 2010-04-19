from django.db import models
from django.conf import settings
from issues.models import *
from utils import parse_ymd
import os.path
import datetime

class Publication(models.Model):
    name = models.CharField(max_length=50, db_index=True, unique=True)
    slug = models.SlugField(max_length=50, db_index=True, unique=True,
            help_text="Determines what the name will look like in a URL.")

    def __unicode__(self):
        return self.name

class PDFIssueManager(models.Manager):
    def get_by_date_and_publication(self, y, m, d, pub):
        date = parse_ymd(y, m, d)
        if not date:
            raise PDFIssue.DoesNotExist
        if isinstance(pub, basestring):
            return self.get(date__exact=date, publication__slug=pub)
        else:
            return self.get(date__exact=date, publication=pub)

    def select_pub(self):
        return self.select_related('publication')

class PDFIssue(models.Model):
    date = models.DateField(db_index=True)
    publication = models.ForeignKey(Publication)
    issue = models.ForeignKey(Issue, blank=True, null=True,
            help_text="Use if this PDF issue is also uploaded in web format.")
    page_count = models.PositiveSmallIntegerField(editable=False, default=0)
    objects = PDFIssueManager()

    class Meta:
        ordering = ('-date',)

    def __unicode__(self):
        return u'PDF issue of %s on %s' % (self.publication, self.date)

    @models.permalink
    def get_absolute_url(self):
        y, m, d = date_tuple(self.date)
        return ('pdfissue-detail', (y, m, d, self.publication.slug), {})

    def save(self, **kwargs):
        if self.id is not None:
            self.page_count = max(self.pages.aggregate(models.Max('page_from'),
                    models.Max('page_to')).itervalues())
        super(PDFIssue, self).save(**kwargs)

def get_page_filename(page, dummy=None, extension='pdf'):
    """Generate a nice descriptive filename for the given page."""
    issue = page.pdfissue
    path = ['%02d' % t for t in issue.date.timetuple()[:3]]
    range = None
    if page.page_to is not None:
        if page.page_from == 1 and page.page_to >= 10:
            range = '' # Probably the whole-issue PDF
        elif page.page_from != page.page_to:
            range = '-page%02d-%02d' % (page.page_from, page.page_to)
    if range is None:
        range = '-page%02d' % (page.page_from,)
    pdf = '%s-%s%s.%s' % (issue.publication.slug,
            issue.date.strftime('%Y-%m-%d'), range, extension)
    return os.path.join(*['archive'] + path + [pdf])

class PDFFile(models.Model):
    file = models.FileField(upload_to=get_page_filename)
    pdfissue = models.ForeignKey(PDFIssue, related_name='pages',
            verbose_name='Issue')
    page_from = models.PositiveSmallIntegerField(db_index=True,
            verbose_name='First page')
    page_to = models.PositiveSmallIntegerField(blank=True, null=True,
            verbose_name='Last page',
            help_text="Optional; use only if this is a multi-page PDF")

    def save(self, **kwargs):
        if self.page_to is not None and self.page_to <= self.page_from:
            self.page_to = None
        super(PDFFile, self).save(**kwargs)
        self.pdfissue.save()

    class Meta:
        ordering = ('page_from',)

    def __unicode__(self):
        return unicode(self.file)

    @models.permalink
    def get_absolute_url(self):
        y, m, d = date_tuple(self.pdfissue.date)
        return ('pdfpage-detail', (y, m, d, self.pdfissue.publication.slug,
                                   self.page_from), {})

    @property
    def thumbnail_path(self):
        return get_page_filename(self, extension='jpg')

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
