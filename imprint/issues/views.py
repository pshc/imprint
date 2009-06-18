from django.http import HttpResponseRedirect
from content.models import *
from django.shortcuts import get_object_or_404
from issues.models import *
from utils import renders

@renders('issues/issue_detail.html')
def issue_detail(request, volume, number):
    object = issue = get_object_or_404(Issue, volume=volume, number=number)
    pieces = issue.pieces.all()[:5]
    return locals()

@renders('issues/issue_detail.html')
def latest_issue(request):
    object = issue = Issue.objects.latest_issue()
    pieces = issue.pieces.all()[:5]
    return locals()

@renders('issues/section_detail.html')
def section_detail(request, slug):
    object = get_object_or_404(Section, slug=slug)
    issue = Issue.objects.latest_issue()
    pieces = Piece.objects.filter(section=object, issue=issue)
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
