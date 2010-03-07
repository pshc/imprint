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

def generate_graph(teams, matches):
    graph = []
    round = 1
    results = set((m.winner.index, m.loser.index) for m in matches)
    rowspan = 1
    teams = teams[:]
    while teams:
        rows = []
        remaining = []
        while teams:
            matchup, teams = teams[:2], teams[2:]
            if len(matchup) < 2:
                rows.append(None)
                break
            number = lambda n: matchup[n].index
            if (number(0), number(1)) in results:
                winner = 'first'
                remaining.append(matchup[0])
            elif (number(1), number(0)) in results:
                winner = 'second'
                remaining.append(matchup[1])
            else:
                rows.append(None)
                continue
            rows.append(dict(first=matchup[0], second=matchup[1],
                    winner=winner))
        graph.append(dict(round=round, rowspan=rowspan, matches=rows,
                half_rowspan=rowspan//2))
        round += 1
        rowspan *= 2
        teams = remaining
    return graph

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
