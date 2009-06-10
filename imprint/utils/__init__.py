from django.core.xheaders import populate_xheaders
from django.shortcuts import render_to_response
from django.template import RequestContext

def renders(template, request_context=True, mimetype=None):
    """Shortcut decorator for render_to_response; takes a template filename

    Return a dictionary from your view function to render it.
    Adds debugging niceties if there is a template variable named "object"."""
    def dec(f):
        def new_view(req, *args, **kwargs):
            d = f(req, *args, **kwargs)
            if isinstance(d, dict):
                c = request_context and RequestContext(req) or None
                resp = render_to_response(template, d, context_instance=c,
                                          mimetype=mimetype)
                # If there is a unique object for this view, add headers
                obj = d.get('object')
                if obj is not None:
                    populate_xheaders(req, resp, obj.__class__, obj.pk)
                return resp
            return d
        # Impersonate the original view function
        new_view.__name__ = f.__name__
        new_view.__module__ = f.__module__
        return new_view
    return dec

def unescape(html): 
    "Returns the given HTML with ampersands, quotes and carets decoded."
    if not isinstance(html, basestring):
        html = str(html)
    return html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;',
            '>').replace('&quot;', '"').replace('&#39;',"'")

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
