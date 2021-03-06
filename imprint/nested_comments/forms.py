from django import forms
from django.contrib.comments.forms import CommentDetailsForm
from django.contrib.contenttypes.models import ContentType
from nested_comments.models import *
import re

tag_re = re.compile(r'<\s*a\s+[^>]*href', re.I)
bb_re = re.compile(r'\[\s*url(?:=.*?)?\s*\]', re.I)
spam_re = re.compile(r'waterloo\s*tech\s*news', re.I)

class NestedCommentForm(CommentDetailsForm):
    name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=False)
    parent = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_name(self):
        return self.cleaned_data.get('name', '').strip()

    def clean_comment(self):
        text = self.cleaned_data.get('comment', '').strip()
        if tag_re.search(text):
            raise forms.ValidationError("HTML tags are output in plaintext. Please don't use them.")
        elif bb_re.search(text):
            raise forms.ValidationError('BBCode is not supported.')
        elif spam_re.search(text):
            raise forms.ValidationError('Your comment looks like spam.')
        return text

    def clean_url(self):
        if self.cleaned_data.get('url'):
            raise forms.ValidationError("Please don't fill in the URL field.")
        return ''

    def get_comment_model(self):
        return NestedComment

    def get_comment_create_data(self):
        data = super(NestedCommentForm, self).get_comment_create_data()
        parent = int(self.cleaned_data.get('parent') or '0')
        if parent:
            try:
                obj = self.target_object
                parent = NestedComment.objects.get(id=parent,
                        content_type=ContentType.objects.get_for_model(obj),
                        object_pk=obj._get_pk_val())
            except NestedComment.DoesNotExist:
                raise forms.ValidationError('Invalid comment parent.')
        data['nesting'] = NestedComment.objects.get_next_child_nesting(
                    self.target_object, parent or None)
        if 'parent' in data:
            del data['parent']
        return data

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
