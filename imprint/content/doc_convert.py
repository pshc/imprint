#!/usr/bin/env python
from HTMLParser import HTMLParser
import re
import subprocess
import sys

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

def prevent_widow(paragraph):
    first = True
    for i in xrange(len(paragraph) - 1, -1, -1):
        frag = paragraph[i]
        if first:
            frag = frag.rstrip()
        if not frag.startswith('<') and ' ' in frag:
            paragraph[i] = '&nbsp;'.join(frag.rsplit(' ', 1))
            break
        first = False

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
        self.prev_bylines = None

    def warn(self, message, *args):
        self.warnings.append(message % args)

    def write(self, data):
        if not self.ignoring and self.font_tag_level > 0:
            assert self.paragraph is not None
            self.paragraph.append(data)

    def handle_starttag(self, tag, attrs):
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

    def is_paragraph_empty(self):
        for text in self.paragraph:
            if text.strip():
                return False
        return True

    def handle_endtag(self, tag):
        if tag == 'div':
            self.ignoring = True
        if self.ignoring:
            return
        if tag == 'p':
            # Done our paragraph!
            p_class = None
            if self.is_paragraph_empty():
                self.paragraph = None
                return
            if self.handler:
                self.prev = (self.handler.__name__.replace('handle_', ''),
                             self.handler(self))
                p_class, self.paragraph_class = self.paragraph_class, None
                if self.is_paragraph_empty():
                    self.paragraph = None
                    return
            prevent_widow(self.paragraph)
            # OK, actually write the paragraph.
            self.paragraph.insert(0, '<p class="%s">' % p_class if p_class
                                                                else '<p>')
            self.paragraph.append('</p>\n')
            final_text = ''.join(self.paragraph)
            self.document.setdefault('copy',[]).append(final_text)
            self.paragraph = None
        elif tag == 'font':
            self.font_tag_level -= 1
        elif tag in OK_TAGS:
            self.write('</%s>' % OK_TAGS[tag])

    def handle_startendtag(self, tag, attrs):
        if 'tag' == 'br':
            self.write('<br />')
        else:
            self.warn('Unknown self-contained tag "%s"', tag)

    def handle_data(self, data):
        self.write(re.sub(r'\s+', ' ', data))

    def handle_charref(self, name):
        self.write('&#%s;' % name)

    def handle_entityref(self, name):
        self.write('&%s;' % name)

    @handler('Copy: first paragraph')
    def handle_copy(self):
        """Connects a drop cap that has been separated from the paragraph."""
        prev_handler, drop_cap = self.prev
        if prev_handler == 'copy' and drop_cap:
            self.paragraph[0] = '<span class="drop">%s</span>%s' % (drop_cap,
                    self.paragraph[0])
        elif len(self.paragraph) == 1 and len(self.paragraph[0]) < 3:
            return self.clear_paragraph()
        self.paragraph_class = 'first'

    @handler('Byline name')
    @no_tags
    def handle_byline_name(self):
        if self.document and self.document.get('copy'):
            self.finish_document()
        self.document.setdefault('bylines', []).append(self.clear_paragraph())

    @handler('Byline title')
    @no_tags
    def handle_byline_title(self):
        title = self.clear_paragraph()
        try:
            #assert self.prev[0] == 'byline_name'
            bylines = self.document['bylines']
            assert bylines and isinstance(bylines[-1], basestring)
            bylines[-1] = (bylines[-1], title.capitalize())
        except AssertionError:
            self.warn('Orphaned byline title "%s" ignored', title)

    @handler('E-mail address')
    @no_tags
    def handle_email(self):
        # Not always an e-mail address, sometimes a name... oh well
        email = self.clear_paragraph().replace('&mdash;',
                '').replace('&ndash;', '')
        email = email.strip().strip('-').strip() # Yes, two strip()s
        if email.lower().startswith('with files from'):
            self.document['sources'] = email[17:].strip()
        elif '@' in email:
            self.document.setdefault('emails', []).append(email)
        else: # Name at end?
            self.document.setdefault('bylines', []).append('-' + email)

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

    @handler('Briefs headline')
    def handle_briefs(self):
        """Chop up multi-part articles."""
        if self.document:
            self.finish_document()
        self.document['title'] = self.clear_paragraph()

    @handler('jump: See WORD, page X', 'jump: Continued from page x')
    def handle_jump(self):
        self.warn("Jump ignored: %s", ''.join(self.paragraph))
        self.paragraph = []

    def finish_document(self):
        self.document['copy'] = ''.join(self.document.get('copy', []))
        # Preserve bylines if missing from part to part
        if self.prev_bylines and not self.document.get('bylines'):
            self.document['bylines'] = self.prev_bylines[:]
        else:
            self.prev_bylines = self.document.get('bylines')
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
        wv = subprocess.Popen(["wvWare", "-c=utf-8", filename],
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
    converter.feed(html)
    converter.close()
    return (converter.documents, converter.warnings)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >>sys.stderr, "You must supply a doc file to convert."
        sys.exit(-1)
    docs, warnings = doc_convert(sys.argv[1])
    for warning in warnings:
        print >>sys.stderr, "WARNING:", warning
    for doc in docs:
        print 'DOCUMENT'
        print doc.get('title', '')
        print doc.get('emails', [])
        print doc.get('bylines', [])
        print doc['copy']

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
