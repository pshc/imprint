from django import http
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from xml.dom import minidom
from urllib import urlencode
from urllib2 import urlopen

# Bleh, non-idempotent GETs. Well, Kiwi has to fix it, not us

def kiwi_url(action, **kwargs):
    return 'http://kiwi.uwaterloo.ca/user/%s?%s' % (action, urlencode(kwargs))

def kiwi_get(action, **kwargs):
    return urlopen(kiwi_url(action, **kwargs)).read()

def absolutify(local_path):
    return 'http://%s%s' % (Site.objects.get_current().domain, local_path)

def set_kiwi_return_url(request, return_url):
    if return_url.startswith('/'):
        return_url = absolutify(return_url)
    request.session['kiwi_referer'] = return_url

def kiwi_login(request):
    if 'kiwi_referer' not in request.session:
        request.session['kiwi_referer'] = request.META.get('HTTP_REFERER')
    domain = Site.objects.get_current().domain
    url = kiwi_url('login',
            __kiwi_referer__='http://%s%s' % (domain, reverse(kiwi_postback)))
    return http.HttpResponseRedirect(url)

def kiwi_logout(request):
    try:
        del request.session['kiwi_username'], request.session['kiwi_info']
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
    request.session['kiwi_username'] = username
    request.session['kiwi_info'] = get_kiwi_details(username)
    return_to = request.session.get('kiwi_referer')
    if return_to:
        del request.session['kiwi_referer']
    else:
        return_to = absolutify('/')
    return http.HttpResponseRedirect(return_to)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
