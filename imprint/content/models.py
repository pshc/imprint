from django.db import models
from django.utils.html import escape
from people.models import Contributor
from richtext.fields import AdminRichTextField
from volumes.models import Issue

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

class Article(models.Model):
    """A written piece."""
    title = models.CharField(max_length=100, help_text=escape(
            "Headline. Some markup is OK: <em>, <cite>"))
    slug = models.SlugField(max_length=100, db_index=True,
            help_text="Determines the article's URL.")
    deck = models.CharField(max_length=200, blank=True,
            help_text="Optional subheadline.")
    text = AdminRichTextField()

    section = models.ForeignKey(Section, related_name='articles')
    issue = models.ForeignKey(Issue, related_name='articles',
            default=Issue.objects.latest)
    authors = models.ManyToManyField(Contributor, related_name='articles',
            through='ArticleAuthor')

    sources = models.CharField(max_length=150, blank=True,
            help_text='Appears as "With files from ..."')
    live = models.BooleanField(default=True,
            help_text='Visible on site?')

    @property
    def author_names(self):
        return u", ".join(self.authors.values_list('name', flat=True))

    class Meta:
        unique_together = [('issue', 'title'), ('issue', 'slug')]

    def __unicode__(self):
        return self.title

class ArticleAuthor(models.Model):
    """Represents a single authorship entry."""
    contributor = models.ForeignKey(Contributor)
    article = models.ForeignKey(Article)
    # TODO: Obtain default w/ AJAX
    position = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.contributor, self.position)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
