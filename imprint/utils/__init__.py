from django.shortcuts import render_to_response
from django.template import RequestContext

def renders(template, request_context=True, mimetype=None):
    """Shortcut decorator for render_to_response; takes a template filename

    Return a dictionary from your view function to render it."""
    def dec(f):
        def new_view(request, *args, **kwargs):
            d = f(request, *args, **kwargs)
            if isinstance(d, dict):
                c = request_context and RequestContext(request) or None
                return render_to_response(template, d, context_instance=c,
                                          mimetype=mimetype)
            return d
        return new_view
    return dec

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
