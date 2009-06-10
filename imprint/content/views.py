from content.doc_convert import doc_convert, DocConvertException
from content.models import *
from datetime import date
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from issues.models import *
import os
from shutil import move
from utils import renders

PART_TYPES = ((0, '---------'),
              (1, 'Text'),
              (2, 'Image'),
              (3, 'Letter'))

def part_field(type, cls=forms.TextInput):
    for n, nm in PART_TYPES:
        if nm == type:
            return cls(attrs={'class': 'part_fields%d' % (n,)})
    assert False

class PartForm(forms.ModelForm):
    order = forms.IntegerField()
    type = forms.IntegerField(required=True,
            widget=forms.Select(choices=PART_TYPES,
                    attrs={'onchange': 'display_part_fields(this);'}))
    content = forms.FileField()
    title = forms.CharField(max_length=100, required=False,
            widget=part_field('Text'),
            help_text='Optional title for this section of text')
    authors = forms.CharField(widget=part_field('Text'))
    sources = forms.CharField(max_length=200, required=False,
            widget=part_field('Text'),
            help_text='Appears as "With files from ..."')
    cutline = forms.CharField(required=False,
            widget=part_field('Image', cls=forms.Textarea))
    artists = forms.CharField(widget=part_field('Image'))
    author = forms.CharField(max_length=50, widget=part_field('Letter'))
    program = forms.CharField(max_length=50, required=False,
            widget=part_field('Letter'))
    #responding_to = generic.GenericForeignKey()

    def full_clean(self):
        """
        Cleans only data chosen by the type field.
        """
        self._errors = ErrorDict()
        if not self.is_bound:
            return
        self.cleaned_data = {}
        type = int(self.fields['type'].widget.value_from_datadict(self.data,
                self.files, self.add_prefix('type')))
        if type < 1 or type >= len(PART_TYPES):
            return
        # Ignore irrelevant fields
        relaxed = []
        for name, field in self.fields.iteritems():
            cls = field.widget.attrs.get('class', '')
            if 'part_field' in cls and cls != 'part_field%d' % type \
                    and field.required:
                field.required = False
                relaxed.append(field)
        ret = super(PartForm, self).full_clean()
        for field in relaxed:
            field.required = True
        return ret

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

    def cmp_parts(self, part1, part2):
        order1 = self.data.get(part1 + '_order', part1)
        order2 = self.data.get(part2 + '_order', part2)
        return cmp(order1, order2)

    def clean(self):
        data = self.cleaned_data
        self.parts = []
        order = 0
        errors = []
        for k in sorted(self.files, cmp=self.cmp_parts):
            order += 1
            file = self.files[k]
            path = file.temporary_file_path()
            base, ext = os.path.splitext(file.name)
            ext = ext[1:].lower()
            if ext == 'doc':
                try:
                    text = doc_convert(path)
                    part = Text(order=order, body=text)
                except DocConvertException, e:
                    errors.append(str(e))
                    continue
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
                part = Image(order=order, image=new_path)
            else:
                errors.append("You may only upload .doc and image files.")
                continue
            self.parts.append(part)
        if not self.files:
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
        last_field_name = 'part'
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('..')
    else:
        form = PieceForm()
    uploads = ['part%d' % i for i in range(5)]
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
