from django.conf import settings
from django.template import Library
from django.utils.safestring import mark_safe

register = Library()

@register.simple_tag
def googleanalytics():
    key = getattr(settings, 'GOOGLE_ANALYTICS_KEY')
    if not key:
        return ''
    return mark_safe("""<!-- Google Analytics -->
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
try {
var pageTracker = _gat._getTracker("API_KEY");
pageTracker._trackPageview();
} catch(err) {}</script>""".replace('API_KEY', key))

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
