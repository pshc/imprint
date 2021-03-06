import datetime
from django.http import HttpResponsePermanentRedirect
from django.conf import settings
from django.core.cache import cache
from django.core.files import storage
from django.core.xheaders import populate_xheaders
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import dates
from django.utils.http import urlquote
from middleware import get_current_user
import os
import random
import subprocess

def renders(template, request_context=True, mimetype=None):
    """Shortcut decorator for render_to_response; takes a template filename

    Return a dictionary from your view function to render it.
    Adds debugging niceties if there is a template variable named "object"."""
    def dec(f):
        def new_view(req, *args, **kwargs):
            d = f(req, *args, **kwargs)
            if isinstance(d, dict):
                t = d.get('template', template)
                c = request_context and RequestContext(req) or None
                resp = render_to_response(t, d, context_instance=c,
                                          mimetype=mimetype)
                # If there is a unique object for this view, add headers
                obj = d.get('object')
                if obj is not None:
                    populate_xheaders(req, resp, obj.__class__, obj.pk)
                if 'canonical' in d:
                    resp['Content-Location'] = d['canonical']
                header, val = random.choice(extra_headers)
                resp['X-' + header.replace(' ', '-')] = val
                return resp
            return d
        # Impersonate the original view function
        new_view.__name__ = f.__name__
        new_view.__module__ = f.__module__
        return new_view
    return dec

extra_headers = {
    'Godot': 'waiting', 'Coffee': 'hotter and more bitter than Hell itself',
    'They Told Me': '"Kid, you\'re special. You\'ll do great things."'
                    ' You know what? They were right.',
    'Chandrasekhar Limit': '1.4 solar masses', 'Spiral Power': 'infinite',
    'Sagittarius A*': 'four million solar masses',
    'Singularity': 'impossible to observe', 'Buster Machine #7': 'Nono',
    'Schwarzchild Radius': 'decreasing', 'Header': 'mispelled',
    'Kyon-kun': 'denwa', 'Policy 9': 'violated',
    'Lawsuit': 'pending', 'YUKI.N': 'sleeping beauty'}.items()
extra_headers.append(("Schrodinger's cat", 'dead'))
extra_headers.append(("Schrodinger's cat", 'alive'))

def send_file(url):
    response = HttpResponsePermanentRedirect(url)
    if url.startswith(settings.MEDIA_URL):
        response['X-Sendfile'] = settings.MEDIA_ROOT + url[
                len(settings.MEDIA_URL):]
    return response

def unescape(html): 
    "Returns the given HTML with ampersands, quotes and carets decoded."
    if not isinstance(html, basestring):
        html = str(html)
    return html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;',
            '>').replace('&quot;', '"').replace('&#39;',"'")

def cache_with_key(key_func, not_found=object()):
    def decorate(f):
        def decorated(*args, **kwargs):
            key = key_func(*args, **kwargs)
            user = get_current_user()
            key = key + '_staff' + ('Y' if (user and user.is_staff) else 'N')
            cached = cache.get(key, not_found)
            if cached is not not_found:
                return cached
            ret = f(*args, **kwargs)
            cache.set(key, ret)
            return ret
        decorated.__name__ = f.__name__
        decorated.__module__ = f.__module__
        return decorated
    return decorate

def date_tuple(date):
    return (date.year, unicode(dates.MONTHS_3[date.month]), date.day)

def parse_ymd(y, m, d):
    try:
        return datetime.date(int(y), dates.MONTHS_3_REV[m], int(d))
    except:
        return None

def format_ymd(y, m, d):
    date = parse_ymd(y, m, d)
    if date:
        return date.strftime('%Y-%m-%d')

class FileSystemStorage(storage.FileSystemStorage):
    def url(self, name):
        """Urlencode the file path properly."""
        name = '/'.join(map(urlquote, name.split(os.path.sep)))
        return super(FileSystemStorage, self).url(name)

def imagemagick(cmd, *args):
    assert cmd in ('identify', 'convert')
    p = subprocess.Popen((cmd,) + args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise Exception(stderr.strip())
    return stdout.strip()

try:
    imagemagick('identify', '-version')
except Exception, e:
    raise Exception("There is a problem with imagemagick: %s" % e)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
