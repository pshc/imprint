from django.conf import settings
from django.template import Library
from django.utils.html import conditional_escape, strip_tags
from django.utils.http import urlquote
import os
import Image as pil

register = Library()

FIXED_WIDTH = 770
THUMBNAIL_WIDTH = 300
THUMBNAIL_HEIGHT = 300

def thumb_dir(filename, prefix):
    path, file = os.path.split(filename)
    path = os.path.join(path, prefix)
    fsdir = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(os.path.join(fsdir, file)):
        return os.path.join(path, file), True
    if not os.path.exists(fsdir):
        os.mkdir(fsdir)
    return os.path.join(path, file), False

def fit(w, h, mw, mh):
    if w > mw:
        h, w = int(round(float(mw) * float(h) / float(w))), mw
    if h > mh:
        w, h = int(round(float(mh) * float(w) / float(h))), mh
    return w, h

def fit_to_fixed_width(w, h, dest=FIXED_WIDTH):
    return dest, int(round(float(dest) * float(h) / float(w)))

def create_thumbnail(orig, thumb, w, h):
    img = pil.open(os.path.join(settings.MEDIA_ROOT, orig))
    img = img.convert("RGB").resize((w, h), pil.ANTIALIAS)
    dest = os.path.join(settings.MEDIA_ROOT, thumb)
    if img.format == 'JPEG':
        img.save(dest, quality=90)
    else:
        img.save(dest)

@register.simple_tag
def thumbnail(unit):
    """Renders a small thumbnail for the given image."""
    image = unit.image
    path, exists = thumb_dir(image.name, 'thumbnail')
    w, h = fit(image.width, image.height, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
    if not exists:
        create_thumbnail(image.name, path, w, h)
    extra = ''
    if unit.cutline:
        alt = strip_tags(conditional_escape(unit.cutline))
        extra = ' alt="%s" title="%s"' % (alt, alt)
    return '<img src="%s%s" width="%d" height="%d"%s />' % (
            settings.MEDIA_URL, urlquote(path), w, h, extra)

@register.simple_tag
def full_thumbnail(unit):
    """Renders a large thumbnail for the given image."""
    image = unit.image
    if image.width <= FIXED_WIDTH:
        path = image.name
        w, h = image.width, image.height
    else:
        path, exists = thumb_dir(image.name, 'fullthumb')
        w, h = fit_to_fixed_width(image.width, image.height)
        if not exists:
            create_thumbnail(image.name, path, w, h)
    return '<img src="%s%s" width="%d" height="%d" />' % (
            settings.MEDIA_URL, urlquote(path), w, h)

@register.inclusion_tag('content/image_legend.html')
def shortimagelegend(image):
    cutline = image.cutline
    if len(cutline) > 80:
        shortened = cutline[:80] + cutline[80:].split(' ', 1)[0]
        if len(shortened) + 6 < cutline:
            cutline = strip_tags(shortened)
            cutline_link = True
    return locals()

@register.inclusion_tag('content/image_legend.html')
def fullimagelegend(image):
    return {'image': image, 'cutline': image.cutline}

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
