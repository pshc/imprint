from django.contrib.sites.models import Site

def current_site(request):
    """Provides the current site as `site` in the context"""
    try:
        site = Site.objects.get_current()
        return {'site': site}
    except Site.DoesNotExist:
        return {'site': None}

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
