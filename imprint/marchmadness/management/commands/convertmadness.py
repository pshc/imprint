from django.conf import settings
from django.core.management import base

def convert():
    from marchmadness.models import Contestant, Entry, Pick, Team, Match
    for c in Contestant.objects.all():
        e = Entry.objects.create(is_redo=False, contestant=c,
                final_score_1=c.final_score_1, final_score_2=c.final_score_2,
                bracket_score=c.bracket_score or 0)
        for p in c.picks.all():
            p.entry = e
            p.save()

class Command(base.NoArgsCommand):
    help = "Convert the old march madness schema."
    def handle_noargs(self, verbosity=0, **options):
        convert()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
