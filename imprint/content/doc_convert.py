#!/usr/bin/env python
from HTMLParser import HTMLParser
import re
import subprocess
import sys

OK_TAGS = {'i': 'em', 'b': 'strong', 's': 'del'}

class DocConverter(HTMLParser):
    def __init__(self, output_stream):
        HTMLParser.__init__(self)
        self.f = output_stream
        self.last_whitespace = True
        self.ignoring = True
        self.paragraph = None

    def write(self, data):
        if not self.ignoring:
            if self.paragraph:
                self.paragraph.append(data)
            else:
                self.f.write(data)

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            self.ignoring = False
        if self.ignoring:
            return
        if tag == 'p':
            if not self.paragraph:
                self.paragraph = ['<p>']
        elif tag == 'br':
            self.write('<br />')
        elif tag in OK_TAGS:
            self.write('<%s>' % OK_TAGS[tag])

    def handle_endtag(self, tag):
        if tag == 'div':
            self.ignoring = True
        elif tag == 'html':
            self.f.write('\n')
        if self.ignoring:
            return
        if tag == 'p':
            if not self.paragraph:
                return
            # Done our paragraph!
            empty = True
            for text in self.paragraph[1:]:
                if text.strip():
                    empty = False
            if not empty:
                final = ''.join(self.paragraph + ['</p>\n'])
                self.paragraph = None
                self.write(final)
            else:
                self.paragraph = None
        elif tag in OK_TAGS:
            self.write('</%s>' % OK_TAGS[tag])

    def handle_startendtag(self, tag, attrs):
        self.write('<br />')

    def handle_data(self, data):
        if self.paragraph and '\t' in data:
            self.paragraph[0] = '<p class="idented">'
        self.write(re.sub(r'\s+', ' ', data))

    def handle_charref(self, name):
        self.write('&#%s;' % name)

    def handle_entityref(self, name):
        self.write('&%s;' % name)

class DocConvertException(Exception):
    pass

def doc_convert(filename, output_stream=None):
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
    stream = output_stream
    if output_stream is None:
        import StringIO
        stream = StringIO.StringIO()
    converter = DocConverter(stream)
    converter.feed(html)
    converter.close()
    if output_stream is None:
        return stream.getvalue()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write("You must supply a doc file to convert.\n")
        sys.exit(-1)
    doc_convert(sys.argv[1], sys.stdout)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
