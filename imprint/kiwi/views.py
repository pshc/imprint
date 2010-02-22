from django import http
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from xml.dom import minidom
from urllib import urlencode
from urllib2 import urlopen
import re

# Bleh, non-idempotent GETs. Well, Kiwi has to fix it, not us

def kiwi_required(func):
    """If kiwi isn't enabled, raises a 404 instead of processing the view."""
    def decorated_view(*args, **kwargs):
        if not getattr(settings, 'KIWI_API_CODE', False):
            raise http.Http404
        return func(*args, **kwargs)
    decorated_view.__name__ = func.__name__
    return decorated_view

def kiwi_url(action, **kwargs):
    return 'http://kiwi.uwaterloo.ca/user/%s?%s' % (action, urlencode(kwargs))

def kiwi_get(action, **kwargs):
    return urlopen(kiwi_url(action, **kwargs)).read()

def absolutify(local_path):
    domain = Site.objects.get_current().domain
    # TEMP: Domain debug considerations
    if settings.DEBUG and getattr(settings, 'DEBUG_DOMAIN', False):
        domain = settings.DEBUG_DOMAIN
    return 'http://%s%s' % (domain, local_path)

def set_kiwi_return_url(request, return_url):
    if return_url.startswith('/'):
        return_url = absolutify(return_url)
    request.session['kiwi_referer'] = return_url

@kiwi_required
def kiwi_login(request):
    if 'kiwi_referer' not in request.session:
        request.session['kiwi_referer'] = request.META.get('HTTP_REFERER')
    url = kiwi_url('login',__kiwi_referer__=absolutify(reverse(kiwi_postback)))
    return http.HttpResponseRedirect(url)

@kiwi_required
def kiwi_logout(request):
    try:
        del request.session['kiwi_info']
    except KeyError:
        pass
    return_to = request.META.get('HTTP_REFERER') or absolutify('/')
    # For some reason, /user/out doesn't work. This does, however.
    return http.HttpResponseRedirect("https://strobe.uwaterloo.ca/cpadev/"
        "kiwi/user/out?__kiwi_referer__=%s" % (return_to,))

def get_kiwi_details(username, attrs=None):
    xml = kiwi_get('find', username=username,
            __kiwi_code__=settings.KIWI_API_CODE)
    doc = minidom.parseString(xml).documentElement
    if attrs is None:
        attrs = ['name', 'firstname', 'lastname', 'email']
    return dict((n.nodeName, n.firstChild.nodeValue) for n in doc.childNodes
            if n.nodeName in attrs)

@kiwi_required
def kiwi_postback(request):
    id = request.GET.get('__kiwi_id__')
    if not id:
        return http.HttpResponseBadRequest('Need an id.')
    xml = kiwi_get('check', id=id, __kiwi_code__=settings.KIWI_API_CODE)
    try:
        doc = minidom.parseString(xml).documentElement
    except:
        if settings.DEBUG:
            raise
        return http.HttpResponseServerError('Kiwi login error')
    username = doc.attributes['username'].value
    info = get_kiwi_details(username)
    # "firstname" contains middle names; guess the first name
    if ' ' in info['firstname']:
        last = info['lastname']
        first, middle = info['firstname'].split(' ', 1)
        info['firstlastname'] = '%s %s' % (first, last)
        mi = [m[0]+'.' for m in re.split(r'[\s-]+', middle)]
        info['middleinitialsname'] = ' '.join([first]+mi+[last])
    info['username'] = username
    request.session['kiwi_info'] = info
    return_to = request.session.get('kiwi_referer')
    if return_to:
        del request.session['kiwi_referer']
    else:
        return_to = absolutify('/')
    return http.HttpResponseRedirect(return_to)

@kiwi_required
def kiwi_toggle(request):
    if not settings.DEBUG:
        raise http.Http404
    if 'kiwi_info' in request.session:
        del request.session['kiwi_info']
        return http.HttpResponse('Unset!')
    else:
        request.session['kiwi_info'] = {'name': 'John Black Smith',
                'firstname': 'John Black', 'lastname': 'Smith',
                'firstlastname': 'John Smith',
                'email': 'pewpew@imprint.uwaterloo.ca',
                'username': 'pewpew'}
        return http.HttpResponse('Set!')

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
