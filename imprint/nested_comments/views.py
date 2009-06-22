from django.shortcuts import get_object_or_404
from nested_comments import get_form
from nested_comments.models import NestedComment
from utils import renders

@renders('comments/preview.html')
def reply(request, id):
    parent = get_object_or_404(NestedComment, id=id)
    object = parent.content_object
    form = get_form()(object, initial={'parent': parent.id})
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
