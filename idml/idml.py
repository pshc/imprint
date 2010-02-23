#!/usr/bin/python

from BeautifulSoup import BeautifulStoneSoup
import os
import simplejson as json
import re

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

def last_text_of(body):
    for text in body[::-1]:
        if not isinstance(text, basestring):
            continue # return ''
        if not text.startswith('<') and not text.endswith('>'):
            return text
    return ''

def change_last_text_of(body, regexp, sub):
    pos = len(body)
    for text in body[::-1]:
        pos -= 1
        assert isinstance(text, basestring)
        if not text.startswith('<') and not text.endswith('>'):
            body[pos] = re.sub(regexp, sub, text)
            return
    assert False, "Should have been able to find the last text"

def unescape_style(style):
    return re.sub(r'\\%([0-9a-fA-F]{2})',
            lambda m: chr(int(m.group(1), 16)), style)

ending_dash_re = re.compile(r'.+[a-zA-Z]-$')

def convert_body(p):
    para_style = unescape_style(
            remove_leading('ParagraphStyle/', p['appliedparagraphstyle']))
    if para_style == 'Ads':
        return []
    body = []
    add = body.append
    for tag in ignore_whitespace(p.contents):
        if tag.name == 'characterstylerange':
            # This isn't really used...?
            #char_style = remove_leading('CharacterStyle/',
            #                            tag['appliedcharacterstyle'])
            stack = []
            push = lambda t: (stack.append(t), add(t))
            # Open modifiers
            style = unescape_style(tag.get('fontstyle', '').strip())
            if style == 'Italic':
                push('<em>')
            elif style in ('Bold', 'Semibold'):
                push('<strong>')
            elif style == 'Regular':
                pass
            elif style:
                push('<span class="%s">' % style)
            # Convert actual content
            for tag in ignore_whitespace(tag.contents):
                if tag.name == 'content':
                    assert len(tag.contents) == 1
                    text = unicode(tag.contents[0])
                    if text.startswith(WHITESPACE) and \
                            not last_text_of(body).endswith('&shy;'):
                        add(' ')
                    add(text.strip())
                    if text.endswith(WHITESPACE):
                        add(' ')
                elif tag.name == 'br':
                    # Convert an ending dash into a soft hyphen
                    if ending_dash_re.match(last_text_of(body)):
                        change_last_text_of(body, r'-$', '&shy;')
                        continue
                    # Need to close and reopen all the current modifiers
                    for tag in stack[::-1]:
                        add(tag_re.sub('</\\1>', tag))
                    add(BREAK)
                    for tag in stack:
                        add(tag)
            # Close modifiers
            for tag in stack[::-1]:
                add(tag_re.sub('</\\1>', tag))
    body = body_to_paragraphs(body)
    if 'NormalParagraphStyle' in para_style:
        return body
    else:
        return [{'_style': para_style, 'body': body}]

def convert_story(dir, story_nm):
    story_fnm = os.path.join(dir, 'Stories', 'Story_%s.xml' % (story_nm,))
    story = BeautifulStoneSoup(file(story_fnm).read())
    story = story.find('story', attrs={'self': story_nm})
    body = []
    for tag in ignore_whitespace(story.contents):
        if tag.name == 'paragraphstylerange':
            body += convert_body(tag)
    return [{'_type': 'story', 'body': body}]

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
    print json.dumps(converted, sort_keys=True, indent=2)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
