from issues.models import Issue

def latest_issue(request):
    try:
        return {'issue': Issue.objects.latest_issue()}
    except Issue.DoesNotExist:
        return {}
