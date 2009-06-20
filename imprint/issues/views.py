import datetime
from django.http import HttpResponseRedirect
from content.models import *
from django.shortcuts import get_object_or_404
from issues.models import *
from utils import renders

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
    except Issue.DoesNotExist:
        pass
    return locals()

@renders('issues/section_detail.html')
def section_detail(request, y, m, d, slug):
    object = get_object_or_404(Section, slug=slug)
    issue = Issue.objects.get_by_date(y, m, d)
    pieces = Piece.objects.filter(section=object, issue=issue)
    return locals()

@renders('issues/section_detail.html')
def section_latest_issue(request, slug):
    object = get_object_or_404(Section, slug=slug)
    issue = Issue.objects.latest_issue()
    pieces = Piece.objects.filter(section=object, issue=issue)
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
