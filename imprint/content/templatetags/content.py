from django import template
from django.conf import settings
from django.core.cache import cache
from django.utils.html import conditional_escape, strip_tags
from django.utils.http import urlquote
import os
import Image as pil
import subprocess

register = template.Library()

# Unit template cache
UNIT_TEMPLATES = {}

@register.tag
def render_unit(parser, token):
    try:
        tag_name, unit = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "render_unit takes one argument"
    return RenderUnitNode(unit)

class RenderUnitNode(template.Node):
    def __init__(self, unit):
        self.unit = template.Variable(unit)

    def render(self, context):
        try:
            unit = self.unit.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        if isinstance(unit, basestring):
            return unit
        # Figure out the unit's type
        type = None
        if isinstance(unit, dict):
            type = unit.get('type')
        if not type:
            return ''
        # Use the type to look up the appropriate template
        if settings.DEBUG or type not in UNIT_TEMPLATES:
            try:
                path = 'content/unit_%s.html' % type.replace(' ', '_')
                tmpl = template.loader.get_template(path)
            except template.TemplateDoesNotExist as e:
                tmpl = None
            UNIT_TEMPLATES[type] = tmpl
        else:
            tmpl = UNIT_TEMPLATES[type]
        if not tmpl:
            return ''
        # Render the obtained template
        context.push()
        context['unit'] = unit
        html = tmpl.render(context)
        context.pop()
        return html

@register.tag
def with_thumbnail(parser, token):
    """Augments the context with information about the image's thumbnail."""
    try:
        tag_name, image, article = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, ("with_thumbnail syntax: "
                "{% with_thumbnail <image> <article> %}...{% endwith %}")
    nodelist = parser.parse(('endwith',))
    parser.delete_first_token()
    return WithThumbnailNode(image, article, nodelist)

class WithThumbnailNode(template.Node):
    def __init__(self, image, article, nodelist):
        self.image = template.Variable(image)
        self.article = template.Variable(article)
        self.nodelist = nodelist

    def __repr__(self):
        return '<WithThumbnailNode>'

    def render(self, context):
        image = self.image.resolve(context)
        article = self.article.resolve(context)
        path = '%(publication)s/vol%(volume)02d/issue%(issue)02d' % article
        cache_key = ('%s/%s' % (path, image['filename']))
        info = cache.get(cache_key)
        if not info:
            info = thumbnail_info(image, article, path)
            cache.set(cache_key, info)
        context.push()
        context.update(info)
        html = self.nodelist.render(context)
        context.pop()
        return html

def thumbnail_info(image, article, path):
    abs_path = os.path.join(settings.MEDIA_ROOT,
            path.replace('/', os.path.sep), image['filename'])
    dim = imagemagick('identify', '-format', '%[fx:w] %[fx:h]', abs_path)
    width, height = map(int, dim.split())
    return dict(width=width, height=height,
            image=settings.MEDIA_URL + path + '/' + image['filename'])

def imagemagick(cmd, *args):
    assert cmd in ('identify', 'mogrify')
    p = subprocess.Popen((cmd,) + args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise Exception(stderr.strip())
    return stdout.strip()

try:
    imagemagick('identify', '-version')
except Exception as e:
    raise Exception("There is a problem with imagemagick: %s" % e)

# old code

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
def thumbnail_width(unit):
    image = unit.image
    w, h = fit(image.width, image.height, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
    return '%d' % w

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
def full_thumbnail_width(unit):
    image = unit.image
    if image.width <= FIXED_WIDTH:
        w = image.width
    else:
        w, h = fit_to_fixed_width(image.width, image.height)
    return '%d' % w

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
    if len(cutline) > 100:
        shortened = cutline[:100] + cutline[100:].split(' ', 1)[0]
        if len(shortened) < len(cutline) - 50:
            cutline = strip_tags(shortened)
            cutline_link = True
    return locals()

@register.inclusion_tag('content/image_legend.html')
def fullimagelegend(image):
    return {'image': image, 'cutline': image.cutline}

@register.inclusion_tag('content/copy_bylines.html')
def renderbylines(copy):
    return {'copy': copy}

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
