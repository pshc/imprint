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
    added_on = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name_plural = 'matches'
        ordering = ['-added_on']

    def __unicode__(self):
        return u'%s won %d-%d against %s' % (self.winner, self.winner_score,
                self.loser_score, self.loser)

    def save(self, **kwargs):
        super(Match, self).save(**kwargs)
        recalculate_all_scores()

    def delete(self, **kwargs):
        super(Match, self).delete(**kwargs)
        recalculate_all_scores()

class Contestant(models.Model):
    username = models.CharField(max_length=20, blank=True)
    full_name = models.CharField(max_length=50)
    # Migrating these out
    final_score_1 = models.PositiveSmallIntegerField(null=True)
    final_score_2 = models.PositiveSmallIntegerField(null=True)
    bracket_score = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return self.full_name

    @property
    def underscored(self):
        return self.full_name.replace(' ', '_')

    class Meta:
        ordering = ['username']

    @property
    def first_score(self):
        try:
            return unicode(self.entries.get(is_redo=False).bracket_score)
        except Entry.DoesNotExist:
            return ''

    @property
    def second_score(self):
        try:
            return unicode(self.entries.get(is_redo=True).bracket_score)
        except Entry.DoesNotExist:
            return ''

class Entry(models.Model):
    is_redo = models.BooleanField()
    final_score_1 = models.PositiveSmallIntegerField(null=True)
    final_score_2 = models.PositiveSmallIntegerField(null=True)
    bracket_score = models.PositiveSmallIntegerField()
    contestant = models.ForeignKey(Contestant, related_name='entries')

    def __unicode__(self):
        return '%s by %s' % ('Redo entry' if self.is_redo else 'Entry',
                self.contestant)

    class Meta:
        unique_together = [('is_redo', 'contestant')]
        ordering = ['is_redo', '-bracket_score']

class Pick(models.Model):
    # Replacing
    contestant = models.ForeignKey(Contestant, related_name='picks')
    # with
    entry = models.ForeignKey(Entry, related_name='picks')

    round = models.PositiveSmallIntegerField()
    slot = models.PositiveSmallIntegerField()
    team = models.ForeignKey(Team, related_name='picks')

def generate_chart(teams, matches, is_redo, picks=None):
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
        pick = picks.get((round, slot))
        if winner:
            remaining[row] = winner
            a.last_dict['contesting'] = False
            b.last_dict['contesting'] = False
            d['contesting'] = True
            loser.last_dict['lost'] = True
            winner.last_dict = d
        else:
            d['editable'] = True
            d['team'] = pick
        if extra_class in ('left', 'right'):
            d['class'] = ('bottom' if slot % 2 else 'top') + extra_class
        else:
            d['class'] = extra_class
        omitted = is_redo and round < 3
        if not omitted:
            if pick and winner == pick:
                d['class'] += ' correct'
            elif winner:
                d['team'] = pick
                d['class'] += ' incorrect'
        return d

    def champion(left, right): # Special case champion final cell
        final = {}
        a = make_result(left.get(0), left.get(16), 5, final, 'fromleft')
        b = make_result(right.get(32), right.get(48), 5, final, 'fromright',
                1, 32)
        champ = make_result(final.get(0), final.get(32), 6, {}, 'centre champ')
        cell = dict(a=a, champ=champ, b=b)
        span = lambda r, n: [[r]] + [[] for i in xrange(n-1)]
        return span('top', 6) + span(cell, 20) + span('bottom', 6)

    (left_matches, left) = add_teams(0, 32, 'left')
    (right_matches, right) = add_teams(32, 64, 'right')
    for m in right_matches:
        m.reverse()

    return [lm + c + rm for (lm, c, rm)
            in zip(left_matches, champion(left, right), right_matches)]

# This is silly... oh well...
def recalculate_all_scores():
    matches = Match.objects.all()
    for c in Contestant.objects.all():
        for e in c.entries.all():
            e.bracket_score = calculate_score(matches, e.picks.all(),
                    e.is_redo)
            e.save()

# I've made a huge mistake.
def calculate_score(matches, picks, is_redo):
    results = set((m.winner.id, m.loser.id) for m in matches)
    picks = dict(((p.round, p.slot), p.team) for p in picks)
    teams = list(Team.objects.all())
    score = 0
    def add_teams(low, high):
        score = 0
        competitors = {}
        for slot, team in enumerate(teams[low:high]):
            competitors[slot+low] = team
        # Match columns
        span = 2
        for round in xrange(1, 5):
            remaining = {}
            slot = low // (2**round)
            for row in xrange(low, high, span):
                a, b = competitors.get(row), competitors.get(row + span//2)
                score += check_match(**locals())
                slot += 1
            span *= 2
            competitors = remaining
        return (score, competitors)

    def check_match(a=None, b=None, round=None, remaining=None, slot=0, row=0,
                **other):
        winner = None
        if not a or not b:
            pass
        elif (a.id, b.id) in results:
            winner, loser = a, b
        elif (b.id, a.id) in results:
            winner, loser = b, a
        if winner:
            remaining[row] = winner
        multiplier = 2**(round-1)
        if is_redo:
            if round < 3:
                return 0
            else:
                multiplier = 2**(round-3)
        pick = picks.get((round, slot))
        # Yahoo! default scoring method
        return multiplier if (pick and winner == pick) else 0

    def champion(left, right): # Special case champion final cell
        final = {}
        score = 0
        score += check_match(left.get(0), left.get(16), 5, final)
        score += check_match(right.get(32), right.get(48), 5, final, 1, 32)
        score += check_match(final.get(0), final.get(32), 6, {})
        return score

    left_score, left = add_teams(0, 32)
    right_score, right = add_teams(32, 64)
    score = left_score + right_score + champion(left, right)
    return score


# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
