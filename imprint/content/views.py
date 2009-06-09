from content.models import Piece
from django import forms
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from issues.models import Issue, Section, latest_issue_or
from utils import renders
from datetime import date

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

class PieceForm(forms.Form):
    headline = forms.CharField(max_length=100)
    slug = forms.SlugField(max_length=100)
    deck = forms.CharField(max_length=200, required=False)
    section = forms.ModelChoiceField(Section)
    issue = forms.IntegerField(initial=latest_issue_or(lambda i: i.number, ''))
    volume = forms.IntegerField(initial=latest_issue_or(lambda i: i.volume,''))
    is_live = forms.BooleanField(required=False)

@permission_required('content.can_add_piece')
@renders('content/piece_create.html')
def piece_create(request):
    title = 'Add piece'
    if request.method == 'POST':
        form = PieceForm(request.POST, request.FILES)
        if form.is_valid():
            form.parts = []
            for k in sorted(request.FILES):
                file = request.FILES[k]
                form.parts.append({'field_name': k, 'file': file})
    else:
        form = PieceForm()
        form.parts = [{'field_name': 'part%02d' % i} for i in range(10)]
    return locals()

@permission_required('content.can_add_piece')
@renders('content/piece_admin.html')
def piece_admin(request):
    title = 'Pieces'
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
