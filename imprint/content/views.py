from content.doc_convert import doc_convert, DocConvertException
from content.models import *
import datetime
from django import forms
from django.conf import settings
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseRedirect, Http404, \
        HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from issues.models import *
import os
from people.models import Contributor
import re
from shutil import move
from utils import renders, unescape

text_input = lambda: forms.TextInput(attrs={'class': 'vTextField'})
small_input = lambda: forms.TextInput(attrs={'class': 'vSmallField'})

def extract_name_and_position(name):
    m = re.match(r'^\s*(.+?)\s*\((.+)\)\s*$', name)
    return m.groups() if m else (name, "")

def get_or_create_contributor(name, position):
    """Not quite the same as Contributor.objects.get_or_create(...)."""
    try:
        return Contributor.objects.get(name__iexact=name)
    except Contributor.DoesNotExist:
        return Contributor.objects.create(name=name, position=position)

def add_artists(image, artists, type, ids):
    for name, pos in (extract_name_and_position(nm)
                      for nm in artists.split(',') if nm.strip()):
        c = get_or_create_contributor(name, pos)
        ids.add(c.id)
        Artist.objects.create(image=image, contributor=c, type=type)

def add_bylines(text, bylines, ids):
    for name, pos in (extract_name_and_position(nm)
                      for nm in bylines.split(',') if nm.strip()):
        c = get_or_create_contributor(name, pos)
        ids.add(c.id)
        Byline.objects.create(text=text, contributor=c, position=pos)

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
            vol = data['volume']
            del data['volume']
            return Issue.objects.get(number=data['issue'], volume=vol)
        except Issue.DoesNotExist:
            raise forms.ValidationError("There is no such issue.")

    def is_part(self, part):
        return re.match(r"part\d+-order", part)
    
    def part_cmp(self, p1, p2):
        return cmp(int(self.data[p1]), int(self.data[p2]))

    def format_byline(self, byline):
        if isinstance(byline, tuple):
            if byline[1]: # Position?
                return u'%s (%s)' % tuple(map(unescape, byline))
            byline = byline[0]
        return unescape(byline)

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
                fields = ['image', 'cutline', 'photographers', 'artists',
                        'courtesy']
            elif attr('copy') is not None:
                part = {'type': 'Text'}
                fields = ['title', 'copy', 'sources', 'bylines']
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
            # Figure out what kind of file this is...
            file = self.files[k]
            path = file.temporary_file_path()
            base, ext = os.path.splitext(file.name)
            ext = ext[1:].lower()
            if ext == 'doc':
                try:
                    (docs, warnings) = doc_convert(path)
                    errors += ["%s: %s" % (file.name, w) for w in warnings]
                except DocConvertException, e:
                    errors.append(str(e))
                    continue
                for doc in docs:
                    if not doc.get('copy', '').strip():
                        errors.append("Omitted an empty section of %s."
                                % file.name)
                        continue
                    bylines = map(self.format_byline, doc.get('bylines', []))
                    order += 1
                    self.parts.append({'type': 'Text', 'order': order,
                        'class': 'errors', 'name': 'part%02d' % order,
                        'title': doc.get('title', ''), 'copy': doc['copy'],
                        'sources': unescape(doc.get('sources', '')),
                        'bylines': ', '.join(bylines)})

            elif ext in ('gif', 'jpg', 'jpeg', 'png', 'tiff'):
                order += 1
                part = {'order': order, 'name': 'part%02d' % order,
                        'class': 'errors'}
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
                        'cutline': '', 'photographers': '', 'artists': '',
                        'courtesy': ''})
                self.parts.append(part)
            else:
                errors.append("You may only upload .doc and image files.")
                continue
        if not self.parts and not self.files:
            errors.append("You must upload at least one portion of content.")
        if errors:
            raise forms.ValidationError(errors)
        return data

    def save(self):
        deleted_fields = ['type', 'name']
        preserved_fields = ['photographers', 'artists', 'bylines']
        piece = Piece(**self.cleaned_data)
        piece.save()
        ids = set()
        for part in self.parts:
            construct = eval(part['type'])
            for field in deleted_fields:
                del part[field]
            preserved = dict((f, '') for f in preserved_fields)
            for field in preserved_fields:
                if field in part:
                    preserved[field] = part[field]
                    del part[field]
            # OK, finally actually make this part...
            part = construct(piece=piece, **part)
            part.save()
            add_artists(part, preserved['photographers'], PHOTOGRAPHER, ids)
            add_artists(part, preserved['artists'], GRAPHIC_ARTIST, ids)
            add_bylines(part, preserved['bylines'], ids)
        # Denormalized list of contributors for the whole piece
        piece.contributors = ids
        piece.save()
        return piece

@permission_required('content.can_add_piece')
@renders('content/piece_create.html')
def piece_create(request):
    title = 'Add piece'
    root_path = '../../../'
    if request.method == 'POST':
        form = PieceForm(request.POST, request.FILES)
        if form.is_valid() and form.is_ready:
            piece = form.save()
            LogEntry.objects.log_action(request.user.id,
                    ContentType.objects.get_for_model(piece).id,
                    piece.id, unicode(piece), ADDITION)
            return HttpResponseRedirect('..')
    else:
        form = PieceForm()
        form.is_ready = True
    uploads = ['upload%d' % i for i in range(5)]
    return locals()

def contributor_lookup(request, with_position=False):
    """AJAX contributor search query."""
    query = request.GET.get('q', '').strip()
    limit = max(1, min(20, int(request.GET.get('limit', '10').strip())))
    if not query:
        return HttpResponseBadRequest("{}")
    data = Contributor.objects.filter(name__icontains=query)[:limit]
    if with_position:
        data = (contributor.with_position for contributor in data)
    else:
        data = data.values_list('name', flat=True)
    return HttpResponse('\n'.join(data), mimetype="application/javascript")

@permission_required('content.can_add_piece')
@renders('content/piece_admin.html')
def piece_admin(request):
    title = 'Pieces'
    root_path = '../../'
    if 'issue' not in request.GET or 'volume' not in request.GET:
        try:
            issue = Issue.objects.latest_issue()
            GET_vars = '?issue=%d&volume=%d' % (issue.number, issue.volume)
            return HttpResponseRedirect(GET_vars)
        except Issue.DoesNotExist:
            pieces_count = "You must create an issue before you add a"
            GET_vars = '?'
    else:
        issue = get_object_or_404(Issue, number=request.GET['issue'],
                volume=request.GET['volume'])
        GET_vars = '?issue=%d&volume=%d' % (issue.number, issue.volume)
        pieces = issue.pieces.select_related().all()
        filter_section = int(request.GET.get('section', -1))
        if filter_section != -1:
            pieces = pieces.filter(section=filter_section)
        sections = issue.sections.all()
        pieces_count = pieces.count()
    return locals()

@renders('content/piece_detail.html')
def piece_detail(request, y, m, d, section, slug):
    """Display the requested piece."""
    issue = Issue.objects.get_by_date(y, m, d)
    object = Piece.objects.get_by_issue_section_slug(issue, section, slug)
    parts = object.parts
    return locals()

@renders('content/image_detail.html')
def image_detail(request, y, m, d, section, slug, image):
    """Display the image in full resolution with comments."""
    issue = Issue.objects.get_by_date(y, m, d)
    piece = Piece.objects.get_by_issue_section_slug(issue, section, slug)
    image = os.path.join(issue.media_dir, image)
    object = get_object_or_404(Image, piece=piece, image=image)
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
