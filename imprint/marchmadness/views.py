from content.models import Piece
from django import http
from issues.models import Issue
from models import *
import re
from utils import renders

def get_relevant_article():
    issue = object = section = None
    try: # to keep the relevant issue/piece in context
        issue = Issue.objects.get(number=42, volume=32) # TODO
        object = issue.pieces.get(slug='march-madness')
        section = object.section
    except (Issue.DoesNotExist, Piece.DoesNotExist):
        pass
    return (issue, object, section)

@renders('marchmadness/index.html')
def index(request):
    issue, object, section = get_relevant_article()
    teams = Team.objects.all()
    # TEMP
    (contestant, cr) = Contestant.objects.get_or_create(username='pshcolli')
    picks = Pick.objects.filter(contestant=contestant)
    chart = generate_chart(teams, Match.objects.all(), picks)
    picks = dict(("round-%d-slot-%d" % (p.round, p.slot), str(p.team.slug))
                for p in picks)
    return locals()

def save_picks(request):
    if request.method != 'POST':
        return http.HttpBadRequest('GET required.')
    # TEMP
    (contestant, cr) = Contestant.objects.get_or_create(username='pshcolli')
    contestant.picks.all().delete()
    try:
        for key, team in request.POST.iteritems():
            m = re.match(r'round-(\d+)-slot-(\d+)$', key)
            if not m:
                continue
            round, slot = int(m.group(1)), int(m.group(2))
            team = Team.objects.get(slug=team)
            Pick.objects.create(round=round, slot=slot, team=team,
                    contestant=contestant)
    except Exception as e:
        return http.HttpResponseServerError(str(e) if settings.DEBUG else
                'A server error occurred; could not save.')
    return http.HttpResponse('Saved.')


# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
