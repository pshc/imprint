from django import template
from django.conf import settings
from django.core.cache import cache
from django.utils.html import conditional_escape, strip_tags
from django.utils.http import urlquote
from utils import imagemagick
import os
import Image as pil

register = template.Library()

# TODO: Some kind of @simple_contextual_tag

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
        return render_fragment(unit, context, is_paragraph=True)

def render_fragment(frag, context, is_paragraph=False):
    """Workhorse. Turns JSON into HTML."""
    # If this is just a string or list of strings, take the easy way out
    html = None
    if isinstance(frag, basestring):
        html = frag
    elif isinstance(frag, list):
        html = ''.join(render_fragment(f, context) for f in frag)
    if html is not None:
        return ('<p>%s</p>\n' % html) if is_paragraph else html
    # Figure out the fragment's type
    type = None
    if isinstance(frag, dict):
        type = frag.get('type')
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
    # Render the obtained template (ignore `is_paragraph`)
    context.push()
    context['unit'] = frag
    html = tmpl.render(context)
    context.pop()
    return html.rstrip()

@register.tag
def dropcap(parser, token):
    try:
        tag_name, unit = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "dropcap takes one argument"
    return DropCapNode(unit)

class DropCapNode(template.Node):
    def __init__(self, unit):
        self.unit = template.Variable(unit)

    def render(self, context):
        try:
            unit = self.unit.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        body = render_fragment(unit['body'], context)
        drop = unit.get('drop')
        if not drop:
            return body
        return '<big>%s</big>%s' % (body[:drop], body[drop:])

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
            info = thumbnail_info(image, path)
            cache.set(cache_key, info)
        context.push()
        context.update(info)
        html = self.nodelist.render(context)
        context.pop()
        return html

THUMBNAIL_FIELDS = ('width', 'height', 'image_src',
        'thumb_width', 'thumb_height', 'thumb_src')

def image_dimensions(abs_path):
    dim = imagemagick('identify', '-format', '%[fx:w]x%[fx:h]', abs_path)
    return map(int, dim.split('x'))

def thumbnail_info(image, path):
    # First get some info about the image itself
    join = os.path.join
    filename = image['filename']
    media_image = join(path.replace('/', os.path.sep), filename)
    abs_image = join(settings.MEDIA_ROOT, media_image)
    width, height = image_dimensions(abs_image)
    # Now generate the thumbnail
    is_full_width = image.get('full-width')
    if is_full_width:
        thumb_width, thumb_height = fit_to_fixed_width(width, height)
        thumb_dir = 'fullthumb'
    else:
        thumb_width, thumb_height = fit(width, height)
        thumb_dir = 'thumbnail'
    media_thumb, thumb_exists = thumb_existence(media_image, thumb_dir)
    abs_thumb = join(settings.MEDIA_ROOT, media_thumb)
    if not thumb_exists:
        thumb_dim = '%dx%d' % (thumb_width, thumb_height)
        imagemagick('convert', '-thumbnail', thumb_dim, abs_image, abs_thumb)
    # Image URLs
    http_path = settings.MEDIA_URL + path
    image_src = '/'.join((http_path, filename))
    thumb_src = '/'.join((http_path, thumb_dir, filename))
    ls = locals()
    return dict((k, ls[k]) for k in THUMBNAIL_FIELDS)

# old code

FIXED_WIDTH = 770
THUMBNAIL_WIDTH = 300
THUMBNAIL_HEIGHT = 300

def thumb_existence(filename, prefix):
    path, file = os.path.split(filename)
    path = os.path.join(path, prefix)
    fsdir = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(os.path.join(fsdir, file)):
        return os.path.join(path, file), True
    if not os.path.exists(fsdir):
        os.mkdir(fsdir)
    return os.path.join(path, file), False

def fit(w, h, mw=THUMBNAIL_WIDTH, mh=THUMBNAIL_HEIGHT):
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
    w, h = fit(image.width, image.height)
    return '%d' % w

@register.simple_tag
def thumbnail(unit):
    """Renders a small thumbnail for the given image."""
    image = unit.image
    path, exists = thumb_existence(image.name, 'thumbnail')
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
        path, exists = thumb_existence(image.name, 'fullthumb')
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
