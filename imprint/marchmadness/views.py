from content.models import Piece
from django import http
from django.contrib.auth.decorators import permission_required
from django.template.defaultfilters import slugify
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
    final_score_1 = contestant.final_score_1 or ''
    final_score_2 = contestant.final_score_2 or ''
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
    parse_maybe = lambda s: int(s) if s else None
    contestant.final_score_1 = parse_maybe(request.POST['final-score-1'])
    contestant.final_score_2 = parse_maybe(request.POST['final-score-2'])
    contestant.save()
    return http.HttpResponse('Saved.')

@permission_required('marchmadness.modify_team')
@renders('marchmadness/edit_teams.html')
def edit_teams(request):
    if request.method == 'POST':
        teams = dict((team.id, team) for team in Team.objects.all())
        seen_slugs = set()
        for n in xrange(1, 65):
            name = request.POST['team-%d' % n]
            if not name:
                continue
            if n in teams:
                team = teams[n]
                team.name = name
                team.save()
                slug = team.slug
            else:
                slug = slugify(name)
                Team.objects.create(id=n, name=name, slug=slug)
            if slug in seen_slugs:
                raise Exception("Identical team slug " + slug)
            seen_slugs.add(slug)
        return http.HttpResponseRedirect(request.path)
    else:
        old = dict(Team.objects.values_list('id', 'name'))
        teams = []
        for n in xrange(1, 65):
            if n in old:
                teams.append(old[n])
                del old[n]
            else:
                teams.append('')
        for invalid in old.itervalues():
            invalid.delete()
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
