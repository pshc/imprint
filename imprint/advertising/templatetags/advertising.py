from django.conf import settings
from django.template import Library
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from imprint.advertising.models import ImageAd

register = Library()

@register.simple_tag
def random_image_ad(type):
    """Renders a random ad of the specified type."""
    try:
        ad = ImageAd.objects.filter(type=int(type),
                is_active=True).order_by('?')[0]
    except IndexError:
        return ''
    alt = conditional_escape(ad.caption)
    url = settings.MEDIA_URL + ad.image.url
    return mark_safe(('<a class="ad" href="%s" title="%s" rel="nofollow">'
                      '<img src="%s" width="%d" height="%d" alt="%s" /></a>')
            % (ad.get_redirect_url(), alt, url, ad.image.width,
                ad.image.height, alt))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
