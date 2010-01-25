from content.models import Piece
from django.http import HttpResponseRedirect
from issues.models import Issue, Section
from models import *
from utils import renders
import datetime

UW_VOTES_PER_DAY = 10
UW_VOTE_INTERVAL = 5*60
EXT_VOTES_PER_DAY = 5
EXT_VOTE_INTERVAL = 30*60

def can_submit_vote(ip, user_agent, cookies):
    if ip == '129.97.194.14': # Imprint office?
        return False
    # This is unreliable but probably Good Enough(TM)
    for cookie in cookies:
        if cookie.startswith('voted'):
            return False

    # Otherwise, throttle votes with a hard cutoff
    uw = ip.startswith('129.97.')
    votes_per_day = UW_VOTES_PER_DAY if uw else EXT_VOTES_PER_DAY
    interval = UW_VOTE_INTERVAL if uw else EXT_VOTE_INTERVAL
    today = datetime.date.today()
    # This would be vulnerable if it didn't record in FRIGGIN' MICROSECONDS
    votes_today = Vote.objects.filter(ip=ip, voted_on__gte=today
            ).values_list('voted_on', flat=True).distinct()

    if votes_today.count() >= votes_per_day:
        return False
    recently = datetime.datetime.now() - datetime.timedelta(seconds=interval)
    try:
        recent_vote = votes_today.get(voted_on__gte=recently)
        return False
    except Vote.DoesNotExist:
        pass
    return True

@renders('feds/index.html')
def feds_index(request):
    try: # to keep the relevant issue/piece in context
        issue = Issue.objects.get(number=23, volume=32)
        object = issue.pieces.get(slug='feds-executive-nominations')
        section = object.section
    except (Issue.DoesNotExist, Section.DoesNotExist, Piece.DoesNotExist):
        pass
    positions = Position.objects.all()
    ip = request.META['REMOTE_ADDR']
    user_agent = request.META['HTTP_USER_AGENT']
    voted_on = datetime.datetime.now()
    can_vote = can_submit_vote(ip, user_agent, request.COOKIES)
    expires = datetime.date.today() + datetime.timedelta(days=1)
    if request.method == 'POST' and can_vote:
        response = HttpResponseRedirect('.')
        for pos in positions:
            try:
                candidate = pos.candidates.get(slug=request.POST.get(pos.slug))
            except Candidate.DoesNotExist:
                continue
            vote = Vote.objects.create(candidate=candidate, ip=ip,
                    user_agent=user_agent, voted_on=voted_on)
            response.set_cookie(str('voted-' + pos.slug),
                    value='No, this is not scientific.',
                    expires=expires.strftime('%a, %d %b %Y %H:%M:%S'))
        return response
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
