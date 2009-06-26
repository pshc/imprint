from django.template import Library
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import re

register = Library()

@register.filter
def togglesqlfields(stmt):
    m = re.match("^SELECT(.+?)FROM(.+)$", stmt)
    if not m:
        return stmt
    return mark_safe('''SELECT <span style="cursor: pointer" onclick="
    $(this).hide(); $(this).next('span').show();
    ">...</span><span style="display: none;">%s</span> FROM %s'''
        % tuple(map(conditional_escape, m.groups())))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
