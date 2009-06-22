from django.contrib.comments.models import Comment
from django.contrib.comments.managers import CommentManager
from django.db import models

MAX_NESTING_LEVEL = 20
MIN_NESTING_CHAR = '0'
MAX_NESTING_CHAR = 'Z'
REVERSE_ORDER_CHAR = '[' # Must be after MAX_NESTING_CHAR
NESTING_DIGITS = 2

NESTING_BASE = ord(MAX_NESTING_CHAR) - ord(MIN_NESTING_CHAR) + 1
# Max number of sibling comments is NESTING_BASE^NESTING_DIGITS

class NestedCommentManager(CommentManager):
    def get_next_child_nesting(self, target_object, parent=None):
        # XXX: Do transactions guarantee unique nesting values?
        comments = NestedComment.objects.for_model(target_object)
        nesting = ''
        if parent:
            nesting = parent.nesting
            comments = comments.filter(nesting__startswith=nesting
                    ).exclude(pk=parent._get_pk_val())
        try:
            last_child = comments.order_by('-nesting')[0]
            n = len(nesting)
            nesting += increment_nesting(
                    last_child.nesting[n:n + NESTING_DIGITS])
        except IndexError:
            nesting += encode_nesting(0)
        return nesting

class NestedComment(Comment):
    objects = NestedCommentManager()
    nesting = models.CharField(max_length=MAX_NESTING_LEVEL * NESTING_DIGITS,
            db_index=True)

    @property
    def indentation(self):
        return len(self.nesting) / NESTING_DIGITS - 1;

    @property
    def poster_name(self):
        return self.name if self.name else 'Anonymous'

    class Meta:
        ordering = ["nesting"]
        #unique_together = [('nesting', 'object_pk', 'content_type')]
        verbose_name = 'comment'

def encode_nesting(num):
    nesting = ''
    for digit in xrange(NESTING_DIGITS, 0, -1):
        c = chr(ord(MIN_NESTING_CHAR) + num % NESTING_BASE)
        if c == REVERSE_ORDER_CHAR:
            raise Exception("Nesting value overflow")
        nesting = c + nesting
        num //= NESTING_BASE
    return nesting

def decode_nesting(nesting):
    assert len(nesting) == NESTING_DIGITS
    num = 0
    while nesting:
        num *= NESTING_BASE
        c, nesting = nesting[0], nesting[1:]
        num += ord(c) - ord(MIN_NESTING_CHAR)
    return num

def increment_nesting(nesting):
    assert len(nesting) == NESTING_DIGITS
    # Could be optimized, who cares
    return encode_nesting(decode_nesting(nesting) + 1)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
