from content.doc_convert import doc_convert, DocConvertException
from content.models import *
import datetime
from django import forms
from django.conf import settings
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import permission_required
from django.db import DatabaseError
from django.http import Http404, HttpResponse, HttpResponseRedirect, \
        HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from issues.models import *
import os
from people.models import Contributor, slugify_name
import re
from shutil import move
from utils import renders, unescape

huge_input = lambda: forms.TextInput(attrs={'class': 'vHugeField'})
small_input = lambda: forms.TextInput(attrs={'class': 'vSmallField'})

def extract_names_and_positions(name):
    """Finds comma-separated names with optional (positions) appended"""
    return re.findall(r'(?!\s)([^,(]+?)\s*(?:\(([^)]+)\)\s*)?,', name+',')

def get_or_create_contributor(name, position):
    """Not quite the same as Contributor.objects.get_or_create(...)."""
    try:
        return Contributor.objects.get(name__iexact=name)
    except Contributor.DoesNotExist:
        try:
            return Contributor.objects.get(slug=slugify_name(name))
        except Contributor.DoesNotExist:
            return Contributor.objects.create(name=name, position=position)

def convert_unit_back(unit):
    if unit.type is Copy:
        copy = unit.copy
        bylines = ', '.join(unicode(b) for b in copy.bylines)
        return {'type': 'Copy', 'id': unit.id,
                'order': unit.order, 'name': 'unit%02d' % unit.order,
                'title': copy.title, 'body': copy.body,
                'sources': copy.sources, 'bylines': bylines}
    elif unit.type is Image:
        image = unit.image
        photographers = ', '.join(Artist.objects.filter(image=image, type=
                PHOTOGRAPHER).values_list('contributor__name', flat=True))
        graphic_artists = ', '.join(Artist.objects.filter(image=image, type=
                GRAPHIC_ARTIST).values_list('contributor__name', flat=True))
        return {'type': 'Image', 'id': unit.id,
                'order': unit.order, 'name': 'unit%02d' % unit.order,
                'image': image.image, 'image_url': image.image.url,
                'cutline': image.cutline, 'courtesy': image.courtesy,
                'photographers': photographers, 'artists': graphic_artists}

def fill_form_from_piece(piece):
    headline, slug, deck = piece.headline, piece.slug, piece.deck
    section = piece.section.id
    volume, issue = piece.issue.volume, piece.issue.number
    series = piece.series and piece.series.id
    is_live, is_featured = piece.is_live, piece.is_featured
    order, id = piece.order, piece.id
    redirect_to = piece.redirect_to
    form = PieceForm(locals())
    form.units = map(convert_unit_back, piece.units)
    return form

class PieceForm(forms.Form):
    headline = forms.CharField(max_length=100, widget=huge_input())
    slug = forms.SlugField(max_length=100, widget=huge_input())
    deck = forms.CharField(max_length=200, required=False, widget=huge_input())
    section = forms.ModelChoiceField(Section.objects)
    volume = forms.IntegerField(initial=latest_issue_or(lambda i: i.volume,''),
            widget=small_input())
    issue = forms.IntegerField(initial=latest_issue_or(lambda i: i.number, ''),
            widget=small_input())
    series = forms.ModelChoiceField(Series.objects, required=False)
    is_live = forms.BooleanField(required=False, initial=False,
            help_text="Public visibility.")
    is_featured = forms.BooleanField(required=False, initial=False,
            help_text="Should this appear in the cover preview?")
    order = forms.IntegerField(required=False, widget=small_input())
    redirect_to = forms.CharField(max_length=100, required=False,
            help_text="If set, redirects to the given URL instead of "
                      "displaying the article.")
    id = forms.IntegerField(required=False)

    def clean_issue(self):
        data = self.cleaned_data
        assert 'volume' in data
        try:
            vol = data['volume']
            del data['volume']
            return Issue.objects.get(number=data['issue'], volume=vol)
        except Issue.DoesNotExist:
            raise forms.ValidationError("There is no such issue.")

    def is_unit(self, unit):
        return re.match(r"unit\d+-order", unit)
    
    def unit_cmp(self, p1, p2):
        return cmp(int(self.data[p1]), int(self.data[p2]))

    def format_byline(self, byline):
        if isinstance(byline, tuple):
            if byline[1]: # Position?
                return u'%s (%s)' % tuple(map(unescape, byline))
            byline = byline[0]
        return unescape(byline)

    def clean(self):
        data = self.cleaned_data
        self.units = getattr(self, 'units', [])
        order = 0
        errors = []
        self.is_ready = True # Since this is a multi-stage form, can we save?
        # Deal with filled-in units
        max_order = 0
        for p in sorted(filter(self.is_unit, self.data), cmp=self.unit_cmp):
            attr = lambda s, d=None: self.data.get(p.replace('order', s), d)
            if attr('image') is not None:
                unit = {'type': 'Image'}
                fields = ['image', 'cutline', 'photographers', 'artists',
                        'courtesy']
            elif attr('body') is not None:
                unit = {'type': 'Copy'}
                fields = ['title', 'body', 'sources', 'bylines']
            else:
                continue
            unit.update(dict((field, attr(field, '')) for field in fields))
            order = int(attr('order'))
            max_order = max(order, max_order)
            unit.update({'order': order, 'name': 'unit%02d' % order})
            if attr('id'):
                unit['id'] = int(attr('id'))
            self.units.append(unit)
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
                    (title, docs, warnings) = doc_convert(path)
                    errors += [u"%s: %s" % (file.name, w) for w in warnings]
                except DocConvertException, e:
                    errors.append(unicode(e))
                    continue
                for doc in docs:
                    if not doc.get('copy', '').strip():
                        errors.append("Omitted an empty section of %s."
                                % file.name)
                        continue
                    bylines = map(self.format_byline, doc.get('bylines', []))
                    order += 1
                    self.units.append({'type': 'Copy', 'order': order,
                        'class': 'errors', 'name': 'unit%02d' % order,
                        'title': doc.get('title', ''), 'body': doc['copy'],
                        'sources': unescape(doc.get('sources', '')),
                        'bylines': ', '.join(bylines)})
            elif ext == 'txt':
                order += 1
                self.units.append({'type': 'Copy', 'order': order,
                    'class': 'errors', 'name': 'unit%02d' % order,
                    'title': '', 'body': open(path).read(),
                    'sources': '', 'bylines': ''})
            elif ext in ('gif', 'jpg', 'jpeg', 'png'):
                order += 1
                unit = {'order': order, 'name': 'unit%02d' % order,
                        'class': 'errors'}
                # TODO: Minor race condition on renaming
                if not data.get('issue'):
                    errors.append("Can't upload images without an issue.")
                    continue
                new_path = data['issue'].get_subdir_filename(file.name)
                try:
                    dest = os.path.join(settings.MEDIA_ROOT, new_path)
                    move(path, dest)
                    os.chmod(dest, 0644)
                except OSError, e:
                    errors.append("Could not save image %s to issue folder."
                            % file.name)
                    continue
                unit.update({'type': 'Image', 'image': new_path,
                        'image_url': settings.MEDIA_URL + new_path,
                        'cutline': '', 'photographers': '', 'artists': '',
                        'courtesy': ''})
                self.units.append(unit)
            else:
                errors.append("You may only upload .doc and image files.")
                continue
        if not self.units and not self.files:
            errors.append("You must upload at least one portion of content.")
        if errors:
            raise forms.ValidationError(errors)
        return data

    def save(self):
        deleted_fields = ['type', 'name']
        preserved_fields = ['photographers', 'artists', 'bylines']
        piece = Piece(**self.cleaned_data)
        # Overwrite if it already exists
        if self.cleaned_data.get('id'):
            piece.contributor_ids = set()
            piece.save(force_update=True)
        else:
            piece.save()
        # Now deal with units
        self.contributor_ids = set() if not piece.series \
              else set(piece.series.contributors.values_list('id', flat=True))
        for unit in self.units:
            construct = {'Copy': Copy, 'Image': Image}[unit['type']]
            for field in deleted_fields:
                del unit[field]
            preserved = dict((f, '') for f in preserved_fields)
            for field in preserved_fields:
                if field in unit:
                    preserved[field] = unit[field]
                    del unit[field]
            # OK, finally actually make this unit...
            u = construct(piece=piece, **unit)
            if 'id' in unit:
                try:
                    u.save(force_update=True)
                except DatabaseError, e:
                    if str(e) != "Forced update did not affect any rows.":
                        pass
            else:
                u.save()
            if construct is Image:
                self.add_artists(u, preserved['photographers'], PHOTOGRAPHER)
                self.add_artists(u, preserved['artists'], GRAPHIC_ARTIST)
            elif construct is Copy:
                self.add_bylines(u, preserved['bylines'])
        # Denormalized list of contributors for the whole piece
        piece.contributors = self.contributor_ids
        piece.save()
        return piece

    def add_artists(self, image, artists, type):
        old_artists = dict(((a.contributor.id, a.type), a)
                for a in image.credits)
        for name, pos in extract_names_and_positions(artists):
            c = get_or_create_contributor(name, pos)
            self.contributor_ids.add(c.id)
            old = (c.id, type)
            if old in old_artists:
                del old_artists[old]
            else:
                Artist.objects.create(image=image, contributor=c, type=type)
        # Clear out any previous credits that no longer exist
        for ((id, t), artist) in old_artists.iteritems():
            if t == type:
                artist.delete()

    def add_bylines(self, copy, bylines):
        old_bylines = dict((b.contributor.id, b) for b in copy.bylines)
        for name, pos in extract_names_and_positions(bylines):
            after_copy, name = name.startswith('-'), name.strip('-').strip()
            if not name:
                continue
            c = get_or_create_contributor(name, pos)
            self.contributor_ids.add(c.id)
            old_byline = old_bylines.get(c.id)
            if old_byline:
                old_byline.position = pos
                old_byline.is_after_copy = after_copy
                old_byline.save()
                del old_bylines[c.id]
            else:
                Byline.objects.create(copy=copy, contributor=c, position=pos,
                        is_after_copy=after_copy)
        # Clear out any old bylines that no longer exist
        for b in old_bylines.itervalues():
            b.delete()

@permission_required('content.add_piece')
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
            return HttpResponseRedirect('..?issue=%d&volume=%d'
                    % (piece.issue.number, piece.issue.volume))
    else:
        form = PieceForm()
        form.is_ready = True
    uploads = ['upload%d' % i for i in range(5)]
    return locals()

@permission_required('content.change_piece')
@renders('content/piece_create.html')
def piece_change(request, id):
    title = 'Change piece'
    root_path = '../../../'
    modifying = True
    id = int(id)
    piece = Piece.objects.get(id=id)
    if request.method == 'POST':
        post = request.POST.copy()
        post['id'] = id
        form = PieceForm(post, request.FILES)
        if form.is_valid() and form.is_ready:
            piece = form.save()
            LogEntry.objects.log_action(request.user.id,
                    ContentType.objects.get_for_model(piece).id,
                    piece.id, unicode(piece), CHANGE)
            return HttpResponseRedirect('..?issue=%d&volume=%d'
                    % (piece.issue.number, piece.issue.volume))
    else:
        form = fill_form_from_piece(piece)
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

def get_issue_and_piece(y, m, d, section, slug):
    try:
        issue = Issue.objects.get_by_date(y, m, d)
        piece = Piece.objects.get_by_issue_section_slug(issue, section, slug)
    except (Issue.DoesNotExist, Piece.DoesNotExist):
        raise Http404
    return (issue, piece)

@renders('content/piece_detail.html')
def piece_detail(request, y, m, d, section, slug):
    """Display the requested piece with comments."""
    if 'c' in request.GET:
        return HttpResponseRedirect('#c%d' % int(request.GET['c']))
    issue, object = get_issue_and_piece(y, m, d, section, slug)
    if object.redirect_to:
        return HttpResponseRedirect(object.redirect_to)
    units = object.units
    preview = object.preview
    if len(units) == 1 and preview[0].is_image \
            and getattr(preview[0].image, 'prominence', '') == 'all':
        # Just an image on its own
        image = preview[0].image
        template = 'content/image_detail.html'
    section = object.section
    return locals()

@renders('content/image_detail.html')
def image_detail(request, y, m, d, section, slug, image):
    """Display the image in full resolution."""
    issue, piece = get_issue_and_piece(y, m, d, section, slug)
    image = os.path.join(issue.media_dir, image)
    image = get_object_or_404(Image, piece=piece, image=image)
    section = image.piece.section
    return locals()

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
