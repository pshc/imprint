from django.core.management import base

class Command(base.NoArgsCommand):
    help = "Displays a dump of all the votes for the Feds poll."
    def handle_noargs(self, **options):
        from feds.models import UserAgent, Vote
        print 'Date\tUser-agent index\tIP\tPosition\tCandidate'
        for vote in Vote.objects.values_list('voted_on', 'user_agent__id',
                'ip', 'candidate__position__slug', 'candidate__slug'):
            print '\t'.join(map(unicode, vote))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
