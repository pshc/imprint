from django.http import HttpResponseRedirect
from issues.models import Issue
from models import *
from utils import renders

@renders('feds/index.html')
def feds_index(request):
    try: # to keep the relevant issue in context
        issue = Issue.objects.get(number=23, volume=32)
    except Issue.DoesNotExist:
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
