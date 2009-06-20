from issues.models import Issue
import re

ymd_re = re.compile(r'^/\d{4}/\d\d?/\d\d?/')

def latest_issue(request):
    if ymd_re.match(request.path):
        return {'is_specific_issue': True}
    try:
        return {'issue': Issue.objects.latest_issue()}
    except Issue.DoesNotExist:
        return {}

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
