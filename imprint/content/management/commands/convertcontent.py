from django.conf import settings
from django.core.management import base
from django.template.defaultfilters import slugify, striptags
import couchdb
import re
import os

conversion_fields = [
    'issue', 'volume', 'publication',
    'section', 'series',
    'headline', 'deck',
    'body', 'redirect_to',
    'contributors',
    'date', 'slug', 'is_live', '_id',
    ]

def convert_piece(piece, verbosity):
    issue, volume = piece.issue.number, piece.issue.volume
    publication = 'imprint'
    section = [piece.section.slug]
    if piece.series:
        series = [piece.series.slug]
    if not piece.series or piece.series.name.lower() != piece.headline.lower():
        headline = piece.headline
    if piece.deck:
        deck = piece.deck
    contributors = set()
    body = []
    subhead_ids = set()
    for unit in piece.units:
        if unit.is_copy:
            convert_copy(unit.copy, body, contributors, subhead_ids)
        elif unit.is_image:
            image = unit.image.image
            new_path = ensure_image_in_right_folder(image.name,
                    publication, volume, issue, verbosity)
            if new_path:
                image.name = new_path
                unit.image.save()
            base = os.path.basename(image.name)
            convert_image(unit.image, base, body, contributors)
    if piece.redirect_to: # Don't store body (only preview) if redirecting
        redirect_to = piece.redirect_to
        del body
    contributors = sorted(contributors)
    slug = piece.slug
    date = piece.issue.date.strftime('%Y-%m-%d')
    is_live = piece.is_live
    # Okay, store everything in a CouchDB document
    ls = locals()
    data = {}
    for field in conversion_fields:
        if field in ls:
            data[field] = ls[field]
    return data

def sane_unique_slugify(src, ids_already_used):
    id = slugify(src)
    if not id:
        id = re.sub('[^\w-]+', '-', src.lower()).strip('-')
        if not id:
            id = 'untitled'
    if len(id) > 30:
        chop = max(min(id.find('-', 25), 25), 40)
        id = id[:chop]
    if id in ids_already_used:
        id = id + '-2'
        while id in ids_already_used:
            id, n = id.rsplit('-', 1)
            id = '%s-%d' % (id, int(n) + 1)
    ids_already_used.add(id)
    return id

def convert_copy(copy, body, contributors, ids_already_used):
    bylines = copy.bylines
    title = striptags(copy.title).strip()
    if title:
        id = sane_unique_slugify(title, ids_already_used)
        body.append(['subhead', id, copy.title.strip()])
    for byline in filter(lambda b: not b.is_after_copy, bylines):
        slug = byline.contributor.slug
        contributors.add(slug)
        body.append(['byline', slug, byline.position])

    body.append(copy.body.strip())

    for byline in filter(lambda b: b.is_after_copy, bylines):
        slug = byline.contributor.slug
        contributors.add(slug)
        body.append(['end-byline', slug])
    if copy.sources:
        body.append(['with-files-from', copy.sources])

def convert_image(image, filename, body, contributors):
    from content.models import PHOTOGRAPHER, GRAPHIC_ARTIST
    figure = dict(type='image', filename=filename)
    if image.cutline:
        figure['cutline'] = image.cutline
    credits = []
    is_photo = False
    is_graphic = False
    for credit in image.credits:
        slug = credit.contributor.slug
        if credit.type == PHOTOGRAPHER:
            credits.append(['photo', slug])
            is_photo = True
        elif credit.type == GRAPHIC_ARTIST:
            credits.append(['graphic', slug])
            is_graphic = True
        contributors.add(slug)
    if image.courtesy:
        credits.append(['courtesy', image.courtesy])
    if credits:
        figure['credits'] = credits
    if is_photo and is_graphic:
        figure['type'] = 'photo-graphic'
    elif is_photo:
        figure['type'] = 'photo'
    elif is_graphic:
        figure['type'] = 'graphic'
    body.append(figure)

def remove_filename_underscore(filename):
    path, ext = os.path.splitext(filename)
    assert ext
    if path.endswith('_'):
        return (path[:-1] + ext, True)
    return (filename, False)

def add_filename_underscore(filename):
    path, ext = os.path.splitext(filename)
    assert ext
    return path + '_' + ext

def ensure_image_in_right_folder(filename, pub, volume, issue, verbosity):
    dir, rel = os.path.split(filename)
    dest = os.path.join(pub, 'vol%02d' % volume, 'issue%02d' % issue)
    if dir == dest:
        return False
    abs = lambda p: os.path.join(settings.MEDIA_ROOT, p)
    dest = os.path.join(dest, rel)
    while os.path.exists(abs(dest)):
        dest, changed = remove_filename_underscore(dest)
        if not changed:
            break
    while os.path.exists(abs(dest)):
        dest = add_filename_underscore(dest)
    if verbosity:
        print 'Moving image %s to %s' % (filename, dest)
    os.rename(abs(filename), abs(dest))
    return dest

def article_id(data):
    return '%(publication)s.%(date)s.%(slug)s' % data

def create_document_from(piece, verbosity):
    from djcouch import db
    if verbosity:
        print 'Converting', piece.issue, '-', piece.slug
    data = convert_piece(piece, verbosity)
    id = article_id(data)
    try:
        db[id] = data
    except couchdb.http.ResourceConflict:
        print 'Overwriting', id
        data['_rev'] = db[id]['_rev']
        db[id] = data

class Command(base.NoArgsCommand):
    help = "Converts DB-backed Pieces to CouchDB."
    def handle_noargs(self, verbosity=0, **options):
        from content.models import Piece
        if verbosity:
            print 'Converting', Piece.objects.count(), 'pieces...'
        for piece in Piece.objects.all():
            create_document_from(piece, verbosity)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
