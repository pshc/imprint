from django.template import Library, loader, Context
from django.utils.safestring import mark_safe
from imprint.advertising.models import ImageAd

register = Library()

IMAGE_AD_TEMPLATE = loader.get_template('advertising/image_ad.html')

@register.simple_tag
def random_image_ad(type):
    """Renders a random ad of the specified type."""
    try:
        ad = ImageAd.objects.filter(type=int(type),
                is_active=True).order_by('?')[0]
        return mark_safe(IMAGE_AD_TEMPLATE.render(Context({'ad': ad})))
    except IndexError:
        return ''

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
