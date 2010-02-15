from django.core.management import base
import os.path

conversion_fields = [
    'issue', 'volume', 'publication',
    'section', 'series',
    'headline', 'deck',
    'body', 'redirect_to',
    'contributors',
    'date', 'slug', 'is_live', '_id',
    ]

def convert_piece(piece, verbosity):
    from content.models import PHOTOGRAPHER, GRAPHIC_ARTIST
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
    if not piece.redirect_to:
        body = []
        for unit in piece.units:
            if unit.is_copy:
                copy = unit.copy
                bylines = copy.bylines
                if copy.title:
                    subhead_id = slugify(copy.title)
                    body.append(['subhead', subhead_id, copy.title])
                for byline in filter(lambda b: not b.is_after_copy, bylines):
                    slug = byline.contributor.slug
                    contributors.add(slug)
                    body.append(['byline', slug, byline.position])
                body.append(copy.body)
                for byline in filter(lambda b: b.is_after_copy, bylines):
                    slug = byline.contributor.slug
                    contributors.add(slug)
                    body.append(['end-byline', slug])
                if copy.sources:
                    body.append(['with-files-from', copy.sources])
            elif unit.is_image:
                image = unit.image
                rel_filename = image.image.name
                # TODO: ensure image is in issue's path
                rel_filename = os.path.basename(self.image.name)
                figure = dict(type='image', filename=rel_filename)
                if image.cutline:
                    figure['cutline'] = image.cutline
                credits = []
                is_photo = False
                is_graphic = False
                for credit in image.credits:
                    slug = byline.contributor.slug
                    if credit.type == PHOTOGRAPHER:
                        credits.append(['photo', slug])
                        contributors.add(slug)
                        is_photo = True
                    elif credit.type == GRAPHIC_ARTIST:
                        credits.append(['graphic', slug])
                        contributors.add(slug)
                        is_graphic = True
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
    else: # Don't store body (only preview) if this is a redirect
        redirect_to = piece.redirect_to
    contributors = sorted(contributors)
    slug = piece.slug
    date = piece.issue.date.strftime('%Y-%m-%d')
    is_live = piece.is_live
    _id = '%s/%s/%s' % (date, publication, slug)
    # Okay, store everything in a CouchDB document
    ls = locals()
    data = {}
    for field in conversion_fields:
        if field in ls:
            data[field] = ls[field]
    return data

class Command(base.NoArgsCommand):
    help = "Converts DB-backed Pieces to CouchDB."
    def handle_noargs(self, verbosity=0, **options):
        from content.models import Piece
        from content import db
        if verbosity:
            print 'Converting', Piece.objects.count(), 'pieces...'
        for piece in Piece.objects.all():
            if verbosity:
                print 'Converting ', piece.issue, piece.slug
            data = convert_piece(piece, verbosity)
            db.create(data)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
