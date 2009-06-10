from content.doc_convert import doc_convert, DocConvertException
from content.models import *
from datetime import date
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from issues.models import *
import os
import re
from shutil import move
from utils import renders, unescape

PART_TYPES = ((0, '---------'),
              (1, 'Text'),
              (2, 'Image'),
              (3, 'Letter'))

def part_field(type, cls=forms.TextInput):
    for n, nm in PART_TYPES:
        if nm == type:
            return cls(attrs={'class': 'part_fields%d' % (n,)})
    assert False

text_input = lambda: forms.TextInput(attrs={'class': 'vTextField'})
small_input = lambda: forms.TextInput(attrs={'class': 'vSmallField'})

class PieceForm(forms.Form):
    headline = forms.CharField(max_length=100, widget=text_input())
    slug = forms.SlugField(max_length=100, widget=text_input())
    deck = forms.CharField(max_length=200, required=False, widget=text_input())
    section = forms.ModelChoiceField(Section.objects)
    volume = forms.IntegerField(initial=latest_issue_or(lambda i: i.volume,''),
            widget=small_input())
    issue = forms.IntegerField(initial=latest_issue_or(lambda i: i.number, ''),
            widget=small_input())
    is_live = forms.BooleanField(required=False, initial=True)

    def clean_issue(self):
        data = self.cleaned_data
        assert 'volume' in data
        try:
            return Issue.objects.get(number=data['issue'],
                    volume=data['volume'])
        except Issue.DoesNotExist:
            raise forms.ValidationError("There is no such issue.")

    def is_part(self, part):
        return re.match(r"part\d+-order", part)
    
    def part_cmp(self, p1, p2):
        return cmp(int(self.data[p1]), int(self.data[p2]))

    def clean(self):
        data = self.cleaned_data
        self.parts = []
        order = 0
        errors = []
        self.is_ready = True # Since this is a multi-stage form, can we save?
        # Deal with filled-in parts
        max_order = 0
        for p in sorted(filter(self.is_part, self.data), cmp=self.part_cmp):
            attr = lambda s, d=None: self.data.get(p.replace('order', s), d)
            if attr('image') is not None:
                part = {'type': 'Image'}
                fields = ['image', 'cutline']
            elif attr('copy') is not None:
                part = {'type': 'Text'}
                fields = ['copy', 'sources']
            else:
                continue
            part.update(dict((field, attr(field, '')) for field in fields))
            order = int(attr('order'))
            max_order = max(order, max_order)
            part.update({'order': order, 'name': 'part%02d' % order})
            self.parts.append(part)
        data = self.cleaned_data
        order = max_order
        # Append any uploaded files
        for k in sorted(self.files):
            self.is_ready = False
            order += 1
            part = {'order': order, 'name': 'part%02d' % order}
            # Figure out what kind of file this is...
            file = self.files[k]
            path = file.temporary_file_path()
            base, ext = os.path.splitext(file.name)
            ext = ext[1:].lower()
            if ext == 'doc':
                try:
                    part['copy'] = doc_convert(path)
                    if not part['copy'].strip():
                        errors.append("%s contained no copy!" % file.name)
                        continue
                except DocConvertException, e:
                    errors.append(str(e))
                    continue
                part.update({'type': 'Text', 'sources': ''})
            elif ext in ('gif', 'jpg', 'jpeg', 'png', 'tiff'):
                # TODO: Minor race condition on renaming
                if not data.get('issue'):
                    errors.append("Can't upload images without an issue.")
                    continue
                new_path = data['issue'].get_subdir_filename(file.name)
                try:
                    dest = os.path.join(settings.MEDIA_ROOT, new_path)
                    move(path, dest)
                except OSError, e:
                    errors.append("Could not save image %s to issue folder."
                            % file.name)
                    continue
                part.update({'type': 'Image', 'image': new_path,
                        'image_url': settings.MEDIA_URL + new_path,
                        'cutline': '', 'class': 'errors'})
            else:
                errors.append("You may only upload .doc and image files.")
                continue
            self.parts.append(part)
        if not self.parts and not self.files:
            errors.append("You must upload at least one portion of content.")
        if errors:
            raise forms.ValidationError(errors)
        return data

@permission_required('content.can_add_piece')
@renders('content/piece_create.html')
def piece_create(request):
    title = 'Add piece'
    root_path = '../../../'
    if request.method == 'POST':
        form = PieceForm(request.POST, request.FILES)
        if form.is_valid() and form.is_ready:
            form.save()
            return HttpResponseRedirect('..')
    else:
        form = PieceForm()
        form.is_ready = True
    uploads = ['upload%d' % i for i in range(5)]
    return locals()

@permission_required('content.can_add_piece')
@renders('content/piece_admin.html')
def piece_admin(request):
    title = 'Pieces'
    root_path = '../../'
    return locals()

@renders('content/piece_detail.html')
def piece_detail(request, y, m, d, section, slug):
    """Display the requested piece."""
    y, m, d = int(y), int(m), int(d)
    issue = get_object_or_404(Issue, date__exact=date(y, m, d))
    object = get_object_or_404(Piece, issue=issue, section__slug=section,
            slug=slug)
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
