from content.models import Piece
from django.http import HttpResponseRedirect
from issues.models import Issue
from models import *
from utils import renders
import datetime

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
    graph = generate_graph(teams, Match.objects.all())
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
