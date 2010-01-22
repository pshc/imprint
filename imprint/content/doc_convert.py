#!/usr/bin/env python
from HTMLParser import HTMLParser
import re
import subprocess
import sys

# TODO: Rewrite with XPath or something

OK_TAGS = {'i': 'em', 'b': 'strong', 's': 'del'}

HANDLERS = {}
def handler(*div_names):
    def decorate(f):
        for name in div_names: HANDLERS[name] = f
        return f
    return decorate

remove_tags = lambda ss: filter(lambda s: not s.startswith('<'), ss)

def no_tags(f):
    def decorated(self, *args, **kwargs):
        self.paragraph = [s.strip() for s in remove_tags(self.paragraph)]
        return f(self, *args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

class DocConverter(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.ignoring = True
        self.paragraph = self.paragraph_class = None
        self.font_tag_level = 0
        self.prev = (None, None)
        self.documents = []
        self.document = {}
        self.warnings = []
        self.title = ''
        self.expecting_title = False # oh god more hacks

    def warn(self, message, *args):
        self.warnings.append(message % args)

    def write(self, data):
        if self.expecting_title:
            self.title += data
        elif not self.ignoring and self.font_tag_level > 0:
            assert self.paragraph is not None
            self.paragraph.append(data)
        elif data.strip():
            self.warn(u'Omitting unknown text: %s', data.strip())

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self.expecting_title = True
        if tag == 'div':
            self.ignoring = False
            self.handler = HANDLERS.get(dict(attrs).get('name'))
        if self.ignoring:
            return
        if tag == 'p':
            if not self.paragraph:
                self.paragraph = []
        elif tag == 'br':
            self.write('<br />')
        elif tag == 'font':
            self.font_tag_level += 1
        elif tag in OK_TAGS:
            self.write('<%s>' % OK_TAGS[tag])

    def clear_paragraph(self):
        ret = ''.join(self.paragraph)
        self.paragraph = []
        return ret

    def has_paragraph_content(self):
        for text in self.paragraph:
            if text.strip():
                return True
        return False

    def call_handler(self):
        if not self.handler:
            return '<p>', '</p>'
        self.prev = (self.handler.__name__, self.handler(self))
        p_class, self.paragraph_class = self.paragraph_class, None
        return ('<p class="%s">' % p_class if p_class else '<p>'), '</p>'

    def handle_endtag(self, tag):
        if tag == 'title':
            self.expecting_title = False
        if tag == 'div':
            self.ignoring = True
        if self.ignoring:
            return
        if tag == 'p':
            # Done our paragraph!
            if self.has_paragraph_content():
                open_tag, close_tag = self.call_handler()
                self.detect_with_files_from()
                if self.has_paragraph_content():
                    # OK, actually write the paragraph.
                    final_text = open_tag + ''.join(self.paragraph) \
                               + close_tag + '\n\n'
                    self.document.setdefault('copy', []).append(final_text)
            self.paragraph = None
        elif tag == 'font':
            self.font_tag_level -= 1
        elif tag in OK_TAGS:
            self.write('</%s>' % OK_TAGS[tag])

    def handle_startendtag(self, tag, attrs):
        if 'tag' == 'br':
            self.write('<br />')
        else:
            self.warn(u'Unknown self-contained tag "%s"', tag)

    def handle_data(self, data):
        self.write(re.sub(r'\s+', ' ', data))

    def handle_charref(self, name):
        self.write('&#%s;' % name)

    def handle_entityref(self, name):
        self.write('&%s;' % name)

    @classmethod
    def strip_dashes(cls, text):
        text = text.strip()
        dashes = True
        if text.startswith('&shy;'):
            text = text[5:].strip()
        if text.startswith('&mdash;'):
            text = text[7:]
        elif text.startswith('&ndash;'):
            text = text[7:]
        elif text.startswith('-'):
            text = text.lstrip('-')
        else:
            dashes = False
        return text.strip(), dashes

    @handler('Copy: first paragraph')
    def handle_copy(self):
        """Connects a drop cap that has been separated from the paragraph."""
        prev_handler, drop_cap = self.prev
        if prev_handler == 'handle_copy' and drop_cap:
            self.paragraph[0] = '<span class="drop">%s</span>%s' % (drop_cap,
                    self.paragraph[0])
        elif 1 <= len(self.paragraph) <= 2:
            drop_cap = ''.join(self.paragraph[:2]).strip()
            if len(drop_cap) < 10:
                return self.clear_paragraph()
        self.paragraph_class = 'first'

    @handler('Byline name')
    @no_tags
    def handle_byline_name(self):
        name = self.clear_paragraph().strip()
        if name:
            if self.document and self.document.get('copy'):
                self.finish_document()
            self.document.setdefault('bylines', []).append(name)

    @handler('Byline title')
    @no_tags
    def handle_byline_title(self):
        title = self.clear_paragraph().strip()
        if title:
            try:
                #assert self.prev[0] == 'byline_name'
                assert 'bylines' in self.document
                bylines = self.document['bylines']
                assert bylines and isinstance(bylines[-1], basestring)
                bylines[-1] = (bylines[-1], title.capitalize())
            except AssertionError:
                self.warn(u'Orphaned byline title "%s" ignored', title)

    @handler('E-mail address', 'Pullquote - with speaker - speaker',
             'Byline editorials and reviews')
    @no_tags
    def handle_end_credit(self):
        credit, had_dash = self.strip_dashes(self.clear_paragraph())
        if self.detect_with_files_from(credit, had_dash):
            pass
        elif '@' in credit:
            self.document.setdefault('emails', []).append(credit)
        else:
            self.document.setdefault('bylines', []).append('-' + credit)

    def detect_with_files_from(self, text=None, dash=None):
        if text is None:
            text, dash = self.strip_dashes(''.join(remove_tags(self.paragraph)))
        if dash and text.lower().startswith('with files from'):
            self.document['sources'] = text[15:].strip()
            self.paragraph = []
            return True
        return False

    @handler('Arts: 1 Band/Film/Author')
    def handle_arts_title(self):
        """Absorbs the first title as the piece's title."""
        self.paragraph_class = 'first'
        if 'title' not in self.document:
            self.paragraph = remove_tags(self.paragraph)
            self.document['title'] = self.clear_paragraph()

    @handler('Arts: 2 Title/Director/Venue', 'Arts: 3 Label/Date/Publisher')
    def handle_arts23(self):
        self.paragraph_class = 'first'

    @handler('Briefs headline', 'Subhead')
    def handle_briefs(self):
        """Chop up multi-part articles."""
        if self.document and set(self.document.keys()) != set(['bylines']):
            self.finish_document()
        title = self.clear_paragraph()
        title = title.replace('<strong>', '').replace('</strong>', '')
        self.document['title'] = title.strip()

    @handler('jump: See WORD,page X', 'jump: See WORD, page X',
             'jump: Continued from page x')
    def handle_jump(self):
        self.warn(u"Jump ignored: %s", ''.join(self.paragraph))
        self.paragraph = []

    def finish_document(self):
        self.document['copy'] = ''.join(self.document.get('copy', []))
        self.documents.append(self.document)
        self.document = {}

    def close(self):
        if self.document:
            self.finish_document()
        HTMLParser.close(self)

class DocConvertException(Exception):
    pass

def doc_convert(filename):
    try:
        wv = subprocess.Popen(["wvWare", "-cutf-8", filename],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True)
    except OSError, e:
        print >>sys.stderr, e
        raise DocConvertException(
                "wvWare is missing; contact your system admin.")
    (html, errors) = wv.communicate()
    if wv.returncode != 0:
        print >>sys.stderr, errors
        raise DocConvertException("wvWare could not process the doc file.")
    converter = DocConverter()
    converter.feed(html.decode('UTF-8'))
    converter.close()
    return (converter.title, converter.documents, converter.warnings)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >>sys.stderr, "You must supply a doc file to convert."
        sys.exit(-1)
    title, docs, warnings = doc_convert(sys.argv[1])
    for warning in warnings:
        print >>sys.stderr, "WARNING:", warning
    for doc in docs:
        print 'DOCUMENT:', title
        print 'Title:', doc.get('title', '')
        print 'Emails:', ', '.join(doc.get('emails', []))
        print 'Bylines:', ', '.join(map(str, doc.get('bylines', [])))
        print 'Sources:', doc.get('sources', '')
        print doc['copy']

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
