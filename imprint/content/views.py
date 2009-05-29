from content.models import Piece
from django.shortcuts import get_object_or_404
from issues.models import Issue
from utils import renders
from datetime import date
 
@renders('content/piece_detail.html')
def article_detail(request, y, m, d, section, slug):
    """Display the requested article."""
    y, m, d = int(y), int(m), int(d)
    issue = get_object_or_404(Issue, date__exact=date(y, m, d))
    object = get_object_or_404(Piece, issue=issue, section__slug=section,
            slug=slug)
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
