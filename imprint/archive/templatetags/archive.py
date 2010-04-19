from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Library
from django.utils.safestring import mark_safe
from utils import date_tuple

register = Library()

@register.simple_tag
def pdfissue_thumbnail_url(pdfissue):
    y, m, d = map(str, pdfissue.date.timetuple()[:3])
    return mark_safe(reverse('pdfissue-thumbnail',
            args=date_tuple(pdfissue.date) + (pdfissue.publication.slug,)))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
