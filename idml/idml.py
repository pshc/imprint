#!/usr/bin/python

from BeautifulSoup import BeautifulStoneSoup
import functools
import os
import simplejson as json
import re

def handler(mapping):
    def decorator(*args):
        if len(args) == 1 and not isinstance(args[0], basestring):
            f = args[0]
            mapping[f.__name__.replace('_', ' ')] = f
            return f
        def wrapper(f):
            mapping.update(dict((name, f) for name in args))
            return f
        return wrapper
    return decorator

CHAR_STYLE_HANDLERS = {}
PARAGRAPH_STYLE_HANDLERS = {}

char_style = handler(CHAR_STYLE_HANDLERS)
paragraph_style = handler(PARAGRAPH_STYLE_HANDLERS)

@char_style
def Italic(state):
    state.open('<em>')

@char_style('Bold', 'Semibold')
def Bold(state):
    state.open('<strong>')

@char_style
def Normal(state):
    pass

@paragraph_style
def Ads(state):
    return []

@paragraph_style('Copy: regular')
def copy_regular(state):
    return state.body

@paragraph_style('Copy: first paragraph')
def copy_first(state):
    return [{'type': 'first', 'body': state.body}]

@paragraph_style
def Byline_name(state):
    return [{'type': 'byline', 'contributor': ' '.join(state.body)}]

@paragraph_style
def Byline_title(state):
    return [{'type': 'byline', 'position': ' '.join(state.body)}]

@paragraph_style
def Subhead(state):
    return [{'type': 'subhead', 'body': state.body}]

def dir_files(dir, extension=None):
    for fnm in os.listdir(dir):
        if extension and not fnm.lower().endswith(extension.lower()):
            continue
        yield os.path.join(dir, fnm)

def ignore_whitespace(contents):
    for c in contents:
        if isinstance(c, basestring):
            assert not c.strip(), "Unexpected free-floating text: " + c.strip()
        else:
            yield c

def remove_leading(prefix, s):
    return s[len(prefix):] if s.startswith(prefix) else s

BREAK = object()
WHITESPACE = (' ', '\n', '\t', '\r')

def body_to_paragraphs(body):
    have_whitespace = False
    paras = []
    cur_para = []
    just_opened = None
    just_closed = None
    for text in body:
        just_reset = True
        if not text:
            pass
        elif text is BREAK:
            cur_para = ''.join(cur_para).strip()
            if cur_para:
                paras.append(cur_para)
            cur_para = []
        elif not text.strip():
            if not have_whitespace:
                have_whitespace = True
                cur_para.append(' ')
        else:
            if text.startswith('</'):
                closer = close_tag_re.match(text).group(1)
                if just_opened == closer:
                    cur_para.pop()
                    just_opened = just_closed = None
                    continue
                just_closed = closer
                just_reset = False
            elif text.startswith('<') and text.endswith('/>'):
                pass
            elif text.startswith('<'):
                opener = tag_re.match(text).group(1)
                if just_closed == opener:
                    cur_para.pop()
                    just_closed = just_opened = None
                    continue
                just_opened = opener
                just_reset = False
            have_whitespace = False
            cur_para.append(text)
        if just_reset:
            just_opened = just_closed = None
    cur_para = ''.join(cur_para).strip()
    if cur_para:
        paras.append(cur_para)
    return paras

tag_re = re.compile(r'<(\w+)\s*[^>]*>$')
close_tag_re = re.compile(r'</(\w+)>$')

def unescape_style(style):
    return re.sub(r'\\%([0-9a-fA-F]{2})',
            lambda m: chr(int(m.group(1), 16)), style)

ending_dash_re = re.compile(r'.+[a-zA-Z]-$')

class BodyState:
    def __init__(self):
        self.stack = []
        self.body = []
    def add(self, text):
        self.body.append(text)
    def open(self, tag):
        self.add(tag)
        self.stack.append(tag)
    def br(self):
        # Need to close and reopen all the current modifiers
        for tag in self.stack[::-1]:
            self.add(tag_re.sub('</\\1>', tag))
        self.add(BREAK)
        for tag in self.stack:
            self.add(tag)
    def close_tags(self):
        # Close modifiers
        for tag in self.stack[::-1]:
            self.add(tag_re.sub('</\\1>', tag))
        self.stack = []

def convert_body(p):
    para_style = unescape_style(
            remove_leading('ParagraphStyle/', p['appliedparagraphstyle']))
    state = BodyState()
    for tag in ignore_whitespace(p.contents):
        if tag.name == 'characterstylerange':
            # This isn't really used...?
            #char_style = remove_leading('CharacterStyle/',
            #                            tag['appliedcharacterstyle'])
            # Open modifiers
            style = unescape_style(tag.get('fontstyle', '').strip())
            if style in CHAR_STYLE_HANDLERS:
                CHAR_STYLE_HANDLERS[style](state)
            elif style:
                state.open('<span class="%s">' % style)
            # Convert actual content
            for tag in ignore_whitespace(tag.contents):
                if tag.name == 'content':
                    assert len(tag.contents) == 1
                    text = unicode(tag.contents[0])
                    if text.startswith(WHITESPACE):
                        state.add(' ')
                    state.add(text.strip())
                    if text.endswith(WHITESPACE):
                        state.add(' ')
                elif tag.name == 'br':
                    state.br()
            state.close_tags()
    # Cleanup and dispatch on paragraph style
    state.body = body_to_paragraphs(state.body)
    if para_style in PARAGRAPH_STYLE_HANDLERS:
        body = PARAGRAPH_STYLE_HANDLERS[para_style](state)
        assert isinstance(body, list), ("Paragraph style handlers must "
                "return a list")
        return body
    elif 'NormalParagraphStyle' not in para_style:
        return [{'_style': para_style, 'body': state.body}]
    return state.body

def convert_story(dir, story_nm):
    story_fnm = os.path.join(dir, 'Stories', 'Story_%s.xml' % (story_nm,))
    story = BeautifulStoneSoup(file(story_fnm).read())
    story = story.find('story', attrs={'self': story_nm})
    body = []
    for tag in ignore_whitespace(story.contents):
        if tag.name == 'paragraphstylerange':
            body += convert_body(tag)
    return [{'_type': 'story', 'body': body}] if body else []

def convert_image(image):
    filename = image.find('link')['linkresourceuri']
    return [{'_type': 'image', 'filename': filename}]

def convert(dir):
    stuff = []
    for spread_fnm in dir_files(os.path.join(dir, 'Spreads'), '.xml'):
        spread = BeautifulStoneSoup(file(spread_fnm).read())
        for textframe in spread.findAll('textframe'):
            story = convert_story(dir, unicode(textframe['parentstory']))
            stuff += story
        for image in spread.findAll('image'):
            image = convert_image(image)
            stuff += image
    return stuff

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print 'Syntax: %s <file to convert>' % (sys.argv[0],)
        sys.exit(-1)
    else:
        d = sys.argv[1]
    converted = convert(d)
    dump = json.dumps(converted, sort_keys=True, indent=2, ensure_ascii=False)
    print dump.encode('UTF-8')

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
