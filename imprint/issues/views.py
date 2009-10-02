from content.models import *
import datetime
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from issues.models import *
from utils import renders, date_tuple

@renders('issues/issue_detail.html')
def issue_detail(request, y, m, d):
    object = issue = Issue.objects.get_by_date(y, m, d)
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

@renders('issues/section_detail.html')
def section_detail(request, y, m, d, slug):
    section = object = get_object_or_404(Section, slug=slug)
    issue = Issue.objects.get_by_date(y, m, d)
    pieces = Piece.objects.filter(section=object, issue=issue)
    return locals()

# Handles any root-level slug; currently sections or series
@renders('issues/section_detail.html')
def area_detail(request, slug):
    try:
        section = object = Section.objects.get(slug=slug)
        issue = Issue.objects.latest_issue()
        pieces = section.pieces.filter(issue=issue, **filter_live())
        canonical = reverse('section-detail',
                args=date_tuple(issue.date) + (slug,))
        editorships = SectionEditorship.objects.filter()
    except Section.DoesNotExist:
        series = object = get_object_or_404(Series, slug=slug)
        pieces = series.pieces.filter(**filter_live())
        template = 'issues/series_detail.html'
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
