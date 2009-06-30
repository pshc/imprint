from django.conf import settings
from django.template import Library
from django.utils.html import conditional_escape, strip_tags
import os
import Image as pil

register = Library()

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

def fixed_width(w, h, dest):
    return dest, int(round(float(dest) * float(h) / float(w)))

def create_thumbnail(orig, thumb, w, h):
    img = pil.open(os.path.join(settings.MEDIA_ROOT, orig))
    img = img.resize((w, h), pil.ANTIALIAS)
    img.save(os.path.join(settings.MEDIA_ROOT, thumb))

@register.simple_tag
def thumbnail(unit):
    """Renders a small thumbnail for the given image."""
    image = unit.image
    path, exists = thumb_dir(image.name, 'thumbnail')
    w, h = fit(image.width, image.height, 250, 250)
    if not exists:
        create_thumbnail(image.name, path, w, h)
    extra = ''
    if unit.cutline:
        alt = strip_tags(conditional_escape(unit.cutline))
        extra = ' alt="%s" title="%s"' % (alt, alt)
    return '<img src="%s%s" width="%d" height="%d" id="image%d"%s />' % (
            settings.MEDIA_URL, path, w, h, unit.id, extra)

@register.simple_tag
def full_thumbnail(unit):
    """Renders a large thumbnail for the given image."""
    image = unit.image
    path, exists = thumb_dir(image.name, 'fullthumb')
    w, h = fixed_width(image.width, image.height, 570)
    if not exists:
        create_thumbnail(image.name, path, w, h)
    return '<img src="%s%s" width="%d" height="%d" id="image%d" />' % (
            settings.MEDIA_URL, path, w, h, unit.id)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
