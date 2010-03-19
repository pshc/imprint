from django.db import models
from datetime import datetime

class Team(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=20, db_index=True)

    def __unicode__(self):
        return self.name

class Match(models.Model):
    winner = models.ForeignKey(Team, related_name='wins')
    winner_score = models.PositiveSmallIntegerField()
    loser = models.ForeignKey(Team, related_name='losses')
    loser_score = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name_plural = 'matches'

    def __unicode__(self):
        return u'%s won %d-%d against %s' % (self.winner, self.winner_score,
                self.loser_score, self.loser)

class Contestant(models.Model):
    username = models.CharField(max_length=20, blank=True)
    full_name = models.CharField(max_length=50)
    final_score_1 = models.PositiveSmallIntegerField(null=True)
    final_score_2 = models.PositiveSmallIntegerField(null=True)

    def __unicode__(self):
        return self.full_name

    @property
    def underscored(self):
        return self.full_name.replace(' ', '_')

class Pick(models.Model):
    contestant = models.ForeignKey(Contestant, related_name='picks')
    round = models.PositiveSmallIntegerField()
    slot = models.PositiveSmallIntegerField()
    team = models.ForeignKey(Team, related_name='picks')

def generate_chart(teams, matches, picks=None):
    results = set((m.winner.id, m.loser.id) for m in matches)
    picks = dict((((p.round, p.slot), p.team) for p in picks) if picks else [])
    teams = list(teams)
    def add_teams(low, high, extra_class):
        competitors = {}
        dest = []
        # Team column
        for slot, team in enumerate(teams[low:high]):
            slot += low
            d = dict(team=team, round=0, slot=slot, contesting=True)
            if extra_class:
                d['class'] = 'mini' + ('bottom' if slot % 2
                        else 'top') + extra_class
            team.last_dict = d
            dest.append([d])
            competitors[slot] = team
        # Match columns
        span = 2
        for round in xrange(1, 5):
            remaining = {}
            slot = low // (2**round)
            for row in xrange(low, high, span):
                a, b = competitors.get(row), competitors.get(row + span//2)
                dest[row-low].append(make_result(**locals()))
                slot += 1
            span *= 2
            competitors = remaining
        return (dest, competitors)

    def make_result(a=None, b=None, round=None, remaining=None,
                extra_class=None, slot=0, row=0, span=1, **other):
        winner = None
        if not a or not b:
            pass
        elif (a.id, b.id) in results:
            winner, loser = a, b
        elif (b.id, a.id) in results:
            winner, loser = b, a
        d = dict(team=winner, rowspan=span, round=round, slot=slot)
        if winner:
            remaining[row] = winner
            a.last_dict['contesting'] = False
            b.last_dict['contesting'] = False
            d['contesting'] = True
            loser.last_dict['lost'] = True
            winner.last_dict = d
        else:
            d['editable'] = True
            d['team'] = picks.get((round, slot))
        if extra_class in ('left', 'right'):
            d['class'] = ('bottom' if slot % 2 else 'top') + extra_class
        else:
            d['class'] = extra_class
        pick = picks.get((round, slot))
        if pick and winner == pick:
            d['class'] += ' correct'
        elif winner:
            d['team'] = pick
            d['class'] += ' incorrect'
        return d

    def champion(left, right): # Special case champion final cell
        final = {}
        a = make_result(left.get(0), left.get(16), 5, final, 'fromleft')
        champ = make_result(final.get(0), final.get(32), 6, {}, 'centre champ')
        b = make_result(right.get(32), right.get(48), 5, final, 'fromright',
                1, 32)
        cell = dict(a=a, champ=champ, b=b)
        span = lambda r, n: [[r]] + [[] for i in xrange(n-1)]
        return span('top', 6) + span(cell, 20) + span('bottom', 6)

    (left_matches, left) = add_teams(0, 32, 'left')
    (right_matches, right) = add_teams(32, 64, 'right')
    for m in right_matches:
        m.reverse()

    return [lm + c + rm for (lm, c, rm)
            in zip(left_matches, champion(left, right), right_matches)]


# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
