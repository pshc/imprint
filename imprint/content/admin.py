from content.models import *
from django.contrib import admin
from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.forms.util import ErrorDict

class AuthorInline(admin.TabularInline):
    model = Author
    extra = 2

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
    class Meta:
        model = Part
    class Media:
        js = ('js/jquery.js', 'js/jquery-ui.js', 'js/part_form.js')
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

class PartFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(PartFormSet, self).__init__(*args, **kwargs)

    def save_new_objects(self, commit=True):
        self.new_objects = []
        for form in self.extra_forms:
            if not form.has_changed():
                continue
            if self.can_delete and form.cleaned_data.get("DELETE"):
                continue
            self.new_objects.append(self.save_new(form, commit=commit))
            if not commit:
                self.save_forms.append(form)
        return self.new_objects

    def save_new(self, form, commit=True):
        raise hell

class PartInline(admin.options.InlineModelAdmin):
    template = 'content/inline_parts.html'
    model = Part
    extra = 3

    def get_formset(self, request, obj=None, **kwargs):
        kwargs['form'] = PartForm
        kwargs['formset'] = PartFormSet
        return super(PartInline, self).get_formset(request, obj=obj, **kwargs)

class PieceAdmin(admin.ModelAdmin):
    fieldsets = ((None, {'fields': ('headline', 'slug', 'deck')}),
                 ('Placement', {'fields': ('section', 'issue')}),
                 ('Misc', {'fields': ('is_live',)}))
    inlines = (PartInline,)
    prepopulated_fields = {'slug': ('headline',)}
    search_fields = ['headline']
    list_display = ['headline', 'authors', 'section', 'issue', 'is_live']
    list_filter = ['issue', 'section', 'is_live']

class EditorshipInline(admin.TabularInline):
    model = SectionEditorship
    extra = 2

class SectionAdmin(admin.ModelAdmin):
    inlines = (EditorshipInline,)
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Piece, PieceAdmin)
admin.site.register(Section, SectionAdmin)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
