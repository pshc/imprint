from django.core.management import base

class Command(base.NoArgsCommand):
    help = "Recalculates March Madness scores."
    def handle_noargs(self, verbosity=0, **options):
        from marchmadness.models import recalculate_all_scores
        recalculate_all_scores()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
