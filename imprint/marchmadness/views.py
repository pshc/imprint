from content.models import Piece
from django import http
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.shortcuts import redirect, get_object_or_404
from django.template.defaultfilters import slugify
from issues.models import Issue
from kiwi.views import kiwi_required, kiwi_preferred_name, \
        set_kiwi_return_url, get_kiwi_details
from models import *
import re
from utils import renders
import datetime

FIRST_TIPOFF = datetime.datetime(2010, 3, 18, 12, 20) # EST
REDO_OPEN    = datetime.datetime(2010, 3, 22,  0,  0)
REDO_TIPOFF  = datetime.datetime(2010, 3, 25, 19,  0)

def is_first_round_open():
    return datetime.datetime.now() < FIRST_TIPOFF
def is_between_rounds():
    return FIRST_TIPOFF < datetime.datetime.now() < REDO_OPEN
def is_second_round_open():
    return REDO_OPEN < datetime.datetime.now() < REDO_TIPOFF

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
    contestants = Contestant.objects.annotate(
            score=Max('entries__bracket_score')).order_by('-score')[:20]
    matches = Match.objects.all()[:20]
    first_round_open = is_first_round_open()
    between_rounds = is_between_rounds()
    second_round_open = is_second_round_open()
    editable = first_round_open or second_round_open
    if first_round_open:
        tipoff = FIRST_TIPOFF
        edit_url = reverse(choose_picks, args=[None])
    elif second_round_open:
        tipoff = REDO_TIPOFF
        edit_url = reverse(choose_picks, args=['redo-'])
    return locals()

@kiwi_required
@renders('marchmadness/scores.html')
def scores(request):
    normal_entries = Entry.objects.filter(is_redo=False, bracket_score__gt=0).order_by('-bracket_score')
    redo_entries = Entry.objects.filter(is_redo=True, bracket_score__gt=0).order_by('-bracket_score')
    if request.user.is_staff:
        emails = []
        for contestant in Contestant.objects.all():
            has_points = False
            if contestant.first_score:
                if int(contestant.first_score) > 0:
                    has_points = True
            if contestant.second_score:
                if int(contestant.second_score) > 0:
                    has_points = True
            if has_points:
                info = get_kiwi_details(contestant.username, attrs=['email'])
                if 'email' in info:
                    emails.append(info['email'])
    return locals()

def get_or_create_entry(contestant, is_redo):
    is_redo = bool(is_redo)
    try:
        return contestant.entries.get(is_redo=is_redo)
    except Entry.DoesNotExist:
        if is_redo and not is_second_round_open():
            raise http.Http404
        return Entry.objects.create(contestant=contestant, is_redo=is_redo,
                bracket_score=0)

@kiwi_required
@renders('marchmadness/choose_picks.html')
def choose_picks(request, is_redo):
    is_redo = bool(is_redo)
    issue, object, section = get_relevant_article()

    if 'kiwi_info' not in request.session:
        return redirect(index)
    kiwi_username = request.session['kiwi_info']['username']
    contestant = Contestant.objects.get(username=kiwi_username)
    entry = get_or_create_entry(contestant, is_redo)
    picks = entry.picks.all()

    teams = Team.objects.all()
    chart = generate_chart(teams, Match.objects.all(), is_redo, picks)

    final_score_1 = entry.final_score_1 or ''
    final_score_2 = entry.final_score_2 or ''
    picks = dict(("round-%d-slot-%d" % (p.round, p.slot), str(p.team.slug))
                for p in picks)
    editable = is_second_round_open() if is_redo else is_first_round_open()
    return locals()

@kiwi_required
@renders('marchmadness/view_picks.html')
def view_picks(request, is_redo, name):
    issue, object, section = get_relevant_article()

    contestant = get_object_or_404(Contestant,
            full_name=name.replace('_', ' '))
    entry = get_or_create_entry(contestant, is_redo)
    picks = entry.picks.all()

    teams = Team.objects.all()
    chart = generate_chart(teams, Match.objects.all(), is_redo, picks)
    editable = False
    return locals()

@kiwi_required
def save_picks(request):
    if request.method != 'POST':
        return http.HttpResponseBadRequest('GET required.')
    if is_first_round_open():
        is_redo = False
    elif is_second_round_open():
        is_redo = True
    else:
        return http.HttpResponseBadRequest('Submissions are closed.')
    kiwi_username = request.session['kiwi_info']['username']
    contestant = Contestant.objects.get(username=kiwi_username)
    entry = get_or_create_entry(contestant, is_redo)
    entry.picks.all().delete()
    try:
        for key, team in request.POST.iteritems():
            m = re.match(r'round-(\d+)-slot-(\d+)$', key)
            if not m:
                continue
            round, slot = int(m.group(1)), int(m.group(2))
            team = Team.objects.get(slug=team)
            Pick.objects.create(round=round, slot=slot, team=team,
                    entry=entry)
    except Exception, e:
        return http.HttpResponseServerError(str(e) if settings.DEBUG else
                'A server error occurred; could not save.')
    parse_maybe = lambda s: int(s) if s else None
    entry.final_score_1 = parse_maybe(request.POST['final-score-1'])
    entry.final_score_2 = parse_maybe(request.POST['final-score-2'])
    entry.save()
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

def redirect_to_choose_picks():
    if is_first_round_open():
        return redirect('mm-choose-picks')
    return redirect('mm-choose-picks', 'redo-')

@kiwi_required
@renders('marchmadness/create_account.html')
def create_account(request):
    if 'kiwi_info' not in request.session:
        return redirect(index)
    username = request.session['kiwi_info']['username']
    try:
        Contestant.objects.get(username=username)
        return redirect_to_choose_picks()
    except Contestant.DoesNotExist:
        pass
    if request.method == 'POST':
        if not request.POST.get('accepted') == 'on':
            message = 'You must accept the Terms and Conditions to continue.'
        else:
            full_name = kiwi_preferred_name(request)
            Contestant.objects.create(username=username, full_name=full_name)
            return redirect_to_choose_picks()
    issue, object, section = get_relevant_article()
    return locals()

@kiwi_required
def login(request):
    set_kiwi_return_url(request, reverse(create_account))
    return redirect('kiwi-login')

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
