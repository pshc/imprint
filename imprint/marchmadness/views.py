from content.models import Piece
from django import http
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.template.defaultfilters import slugify
from issues.models import Issue
from kiwi.views import kiwi_required, kiwi_preferred_name, set_kiwi_return_url
from models import *
import re
from utils import renders

def get_relevant_article():
    issue = object = section = None
    try: # to keep the relevant issue/piece in context
        issue = Issue.objects.get(number=30, volume=32)
        object = issue.pieces.get(slug='march-madness')
        section = object.section
    except (Issue.DoesNotExist, Piece.DoesNotExist):
        pass
    return (issue, object, section)

@kiwi_required
@renders('marchmadness/index.html')
def index(request):
    issue, object, section = get_relevant_article()
    try:
        kiwi_username = request.session['kiwi_info']['username']
        Contestant.objects.get(username=kiwi_username)
        has_account = True
    except:
        has_account = False
    contestants = Contestant.objects.order_by('-id')[:10]
    return locals()

@kiwi_required
@renders('marchmadness/choose_picks.html')
def choose_picks(request):
    issue, object, section = get_relevant_article()

    kiwi_username = request.session['kiwi_info']['username']
    contestant = Contestant.objects.get(username=kiwi_username)
    picks = contestant.picks.all()

    teams = Team.objects.all()
    chart = generate_chart(teams, Match.objects.all(), picks)

    final_score_1 = contestant.final_score_1 or ''
    final_score_2 = contestant.final_score_2 or ''
    picks = dict(("round-%d-slot-%d" % (p.round, p.slot), str(p.team.slug))
                for p in picks)
    editable = True
    return locals()

@kiwi_required
@renders('marchmadness/view_picks.html')
def view_picks(request, name):
    issue, object, section = get_relevant_article()

    contestant = get_object_or_404(Contestant,
            full_name=name.replace('_', ' '))
    picks = contestant.picks.all()

    teams = Team.objects.all()
    chart = generate_chart(teams, Match.objects.all(), picks)
    editable = False
    return locals()

@kiwi_required
def save_picks(request):
    if request.method != 'POST':
        return http.HttpBadRequest('GET required.')
    kiwi_username = request.session['kiwi_info']['username']
    contestant = Contestant.objects.get(username=kiwi_username)
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
    except Exception, e:
        return http.HttpResponseServerError(str(e) if settings.DEBUG else
                'A server error occurred; could not save.')
    parse_maybe = lambda s: int(s) if s else None
    contestant.final_score_1 = parse_maybe(request.POST['final-score-1'])
    contestant.final_score_2 = parse_maybe(request.POST['final-score-2'])
    contestant.save()
    return http.HttpResponse('Saved.')

@kiwi_required
@permission_required('marchmadness.change_team')
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

@kiwi_required
@renders('marchmadness/create_account.html')
def create_account(request):
    if 'kiwi_info' not in request.session:
        return redirect(index)
    username = request.session['kiwi_info']['username']
    try:
        Contestant.objects.get(username=username)
        return redirect(choose_picks)
    except Contestant.DoesNotExist:
        pass
    if request.method == 'POST':
        if not request.POST.get('accepted') == 'on':
            message = 'You must accept the Terms and Conditions to continue.'
        else:
            full_name = kiwi_preferred_name(request)
            Contestant.objects.create(username=username, full_name=full_name)
            return redirect(choose_picks)
    issue, object, section = get_relevant_article()
    return locals()

@kiwi_required
def login(request):
    set_kiwi_return_url(request, reverse(create_account))
    return redirect('kiwi-login')

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
