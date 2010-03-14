from django.db import models
from datetime import datetime

class Team(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=20, db_index=True)
    index = models.PositiveSmallIntegerField(unique=True, db_index=True)

    class Meta:
        ordering = ['index']

    def __unicode__(self):
        return self.name

class Match(models.Model):
    winner = models.ForeignKey(Team, related_name='wins')
    loser = models.ForeignKey(Team, related_name='losses')

def generate_chart(teams, matches):
    results = set((m.winner.index, m.loser.index) for m in matches)
    teams = list(teams)
    def add_teams(low, high):
        competitors = {}
        dest = []
        # Team column
        for slot, team in enumerate(teams[low:high]):
            d = dict(team=team, round=0, slot=slot, contesting=True)
            team.last_dict = d
            dest.append([d])
            competitors[slot] = team
        # Match columns
        span = 2
        for round in xrange(1, 6):
            remaining = {}
            slot = low // (2**round)
            for row in xrange(low, high, span):
                a, b = competitors.get(row), competitors.get(row + span//2)
                winner = None
                if not a or not b:
                    pass
                elif (a.index, b.index) in results:
                    winner = a
                elif (b.index, a.index) in results:
                    winner = b
                d = dict(team=winner, rowspan=span, round=round, slot=slot)
                if winner:
                    remaining[row] = winner
                    a.last_dict['contesting'] = False
                    b.last_dict['contesting'] = False
                    d['contesting'] = True
                    winner.last_dict['won'] = True
                    winner.last_dict = d
                dest[row-low].append(d)
                slot += 1
            span *= 2
            competitors = remaining
        return dest

    left_matches = add_teams(0, 32)
    right_matches = (l[::-1] for l in add_teams(32, 64))

    return [lm + rm for (lm, rm) in zip(left_matches, right_matches)]


# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
