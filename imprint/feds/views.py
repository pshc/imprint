from content.models import Piece
from django.http import HttpResponseRedirect
from issues.models import Issue, Section
from models import *
from utils import renders

@renders('feds/index.html')
def feds_index(request):
    try: # to keep the relevant issue/piece in context
        issue = Issue.objects.get(number=23, volume=32)
        object = issue.pieces.get(slug='feds-executive-nominations')
        section = object.section
    except (Issue.DoesNotExist, Section.DoesNotExist, Piece.DoesNotExist):
        pass
    positions = Position.objects.all()
    if request.method == 'POST':
        for pos in positions:
            try:
                candidate = pos.candidates.get(slug=request.POST.get(pos.slug))
            except Candidate.DoesNotExist:
                continue
        return HttpResponseRedirect('.')
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
