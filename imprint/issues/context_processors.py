from issues.models import Issue

def latest_issue(request):
    return {'issue': Issue.objects.latest_issue()}
