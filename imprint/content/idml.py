#!/usr/bin/python

from BeautifulSoup import BeautifulStoneSoup
import os

def dir_files(dir, extension=None):
    for fnm in os.listdir(dir):
        if extension and not fnm.lower().endswith(extension.lower()):
            continue
        yield os.path.join(dir, fnm)

def ignore_whitespace(contents):
    for c in contents:
        if isinstance(c, basestring):
            assert not c.strip()
        else:
            yield c

def remove_leading(prefix, s):
    return s[len(prefix):] if s.startswith(prefix) else s

def paragraph(p):
    para_style = remove_leading('ParagraphStyle/', p['appliedparagraphstyle'])
    if 'NormalParagraphStyle' not in para_style:
        print 'STYLE', para_style
    for tag in ignore_whitespace(p.contents):
        if tag.name == 'characterstylerange':
            char_style = remove_leading('CharacterStyle/',
                                        tag['appliedcharacterstyle'])
            if tag.has_key('fontstyle'):
                print 'STYLE', tag['fontstyle'], ':',
            for tag in ignore_whitespace(tag.contents):
                if tag.name == 'content':
                    assert len(tag.contents) == 1
                    text = unicode(tag.contents[0])
                    if text.strip():
                        print text.encode('utf8')
                    else:
                        print '<whitespace>'
                elif tag.name == 'br':
                    print '<br />'

def convert_story(dir, story_nm):
    story_fnm = os.path.join(dir, 'Stories', 'Story_%s.xml' % (story_nm,))
    story = BeautifulStoneSoup(file(story_fnm).read())
    story = story.find('story', attrs={'self': story_nm})
    for tag in ignore_whitespace(story.contents):
        if tag.name == 'paragraphstylerange':
            paragraph(tag)

def convert_image(image):
    filename = image.find('link')['linkresourceuri']
    print 'IMAGE', filename

def convert(dir):
    for spread_fnm in dir_files(os.path.join(dir, 'Spreads'), '.xml'):
        spread = BeautifulStoneSoup(file(spread_fnm).read())
        for textframe in spread.findAll('textframe'):
            convert_story(dir, unicode(textframe['parentstory']))
        for image in spread.findAll('image'):
            convert_image(image)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        d = 'CS4_test_page1'
        #print 'Syntax: %s <file to convert>' % (sys.argv[0],)
        #sys.exit(-1)
    else:
        d = sys.argv[1]
    convert(d)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
