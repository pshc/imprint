from content.models import *
from content.views import with_article_context
import datetime
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
import djcouch
from issues.models import *
from utils import renders, date_tuple, format_ymd

@renders('issues/issue_detail.html')
def issue_detail(request, y, m, d):
    try:
        object = issue = Issue.objects.get_by_date(y, m, d)
    except Issue.DoesNotExist:
        raise Http404
    pieces = issue.pieces.all()[:5]
    return locals()

@renders('issues/issue_detail.html')
def latest_issue(request):
    try:
        object = issue = Issue.objects.latest_issue()
        pieces = issue.pieces.all()[:5]
        canonical = issue.get_absolute_url()
    except Issue.DoesNotExist:
        pass
    return locals()

# XXX: Should we do the lookup by date, or by vol/issue?
# By date: means everything has to be published on the same day
#          (will break web exclusives...)
# By vol/issue: need to maintain a separate (date -> vol/issue) mapping
# This trouble will probably go away if we move to a less issue-oriented format

@renders('issues/tag_detail.html')
@with_article_context
def date_tag_detail(request, y, m, d, pub, slug):
    """
    articles_by_date_and_tag = function(doc) {
        for each (var tag in doc.tags) {
            emit([doc.publication, doc.date, tag].join("."), doc);
        }
    }
    """
    # old code
    try:
        issue = Issue.objects.get_by_date(y, m, d)
    except Issue.DoesNotExist:
        raise Http404
    # new code
    tag = object = djcouch.get_document_or_404(slug, db='tags')
    key = '.'.join((pub, format_ymd(y, m, d), slug))
    articles = [row.value
            for row in djcouch.view('articles_by_date_and_tag', key=key)]
    if object['type'] == 'section' and len(articles) == 1:
        pass # TODO: return redirect(pieces[0])
    return locals()

@renders('issues/tag_detail.html')
@with_article_context
def tag_detail(request, slug):
    """
    articles_by_tag = function(doc) {
        for each (var tag in doc.tags) {
            emit(tag, doc);
        }
    }
    """
    tag = object = djcouch.get_document_or_404(slug, db='tags')
    articles = [row.value for row in djcouch.view('articles_by_tag', key=slug)]
    if object['type'] == 'section' and len(articles) == 1:
        pass # TODO
    return locals()

@renders('issues/section_detail.html')
def section_detail(request, y, m, d, slug):
    try:
        return date_tag_detail(request, y, m, d, 'imprint', slug)
    except Http404:
        pass
    section = object = get_object_or_404(Section, slug=slug)
    try:
        issue = Issue.objects.get_by_date(y, m, d)
    except Issue.DoesNotExist:
        raise Http404
    pieces = Piece.objects.filter(section=object, issue=issue)
    if pieces.count() == 1:
        return redirect(pieces[0])
    return locals()

# Handles any root-level slug; currently sections or series
@renders('issues/section_detail.html')
def area_detail(request, slug):
    try:
        return tag_detail(request, slug)
    except Http404:
        pass
    try:
        section = object = Section.objects.get(slug=slug)
        issue = Issue.objects.latest_issue()
        pieces = section.pieces.filter(issue=issue, **filter_live())
        if pieces.count() == 1:
            return redirect(pieces[0])
        canonical = reverse('section-detail',
                args=date_tuple(issue.date) + (slug,))
        editorships = SectionEditorship.objects.filter()
    except Section.DoesNotExist:
        series = object = get_object_or_404(Series, slug=slug)
        pieces = series.pieces.filter(**filter_live())
        template = 'issues/series_detail.html'
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
