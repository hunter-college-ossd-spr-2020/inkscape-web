#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
#
# This file is part of the software inkscape-web, consisting of custom
# code for the Inkscape project's django-based website.
#
# inkscape-web is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# inkscape-web is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with inkscape-web.  If not, see <http://www.gnu.org/licenses/>.
#
"""
The MimeType field is actually a fake field, it's just a simple object
created when called with a string version of the mime type.

It converts all the weird and wacky mime types out there into more simple
and segregated forms and provides a way to get icons for them.
"""

import re
import os
import mimetypes

from pygments import highlight, lexers, formatters
from pygments.util import ClassNotFound

from django.utils.safestring import mark_safe
from django.conf import settings
from django.core.files.images import get_image_dimensions
from django.contrib.staticfiles import finders, storage

MIME_DIR = 'mime'
#MIME_URL = os.path.join(settings.STATIC_URL, MIME_DIR)
#MIME_ROOT = os.path.join(settings.STATIC_ROOT, MIME_DIR)

ALL_TEXT_TYPES = sorted(dict((mimes[0], name)\
    for (name, alias, patterns, mimes) in lexers.get_all_lexers()\
      if mimes).items(), key=lambda item: item[1])

class CodeHtmlFormatter(formatters.HtmlFormatter):
    """Add html formatter for code diffs"""
    @staticmethod
    def wrap(source, *_):
        """Outputs diff code-lines"""
        yield 0, '<ol id="lines">'
        for i, code in source:
            yield i, "<li><code>%s</code></li>" % code
        yield 0, '</ol>'

def syntaxer(text, mime):
    """Highlights text files based on their type"""
    formatter = CodeHtmlFormatter(encoding='utf8')
    try:
        lexer = lexers.get_lexer_for_mimetype(str(mime))
    except ClassNotFound:
        try:
            lexer = lexers.guess_lexer(text)
        except ClassNotFound:
            return text
    text_bytes = highlight(text, lexer, formatter)
    return mark_safe(text_bytes.decode('utf-8'))

def get_range(text):
    """Turns text 1-2 into two integers as their range"""
    if '-' not in text:
        text = text + '-' + text
    return (force_int(x) for x in text.split('-', 1))

SCALES = ' KMGT'
def force_int(text):
    """Turns 5KB into 5000, and similar conversions"""
    text = text.upper().replace('B', '').strip()
    if text[-1] in ['K', 'M', 'G', 'T']:
        return int(text[:-1]) * (2 ** (SCALES.index(text[-1]) * 10))
    return int(text)

def upto(d, c='resources', blank=True, lots=False):
    """Quick and easy upload to location"""
    dated = lots and ["%Y","%m"] or []
    return dict(null=blank, blank=blank, upload_to=os.path.join(c, d, *dated))

def static(*parts):
    name = os.path.join(*parts)
    return storage.staticfiles_storage.url(name)

def cached(f):
    _cname = '_'+f.__name__
    def _inner(self):
        if not hasattr(self, _cname):
            setattr(self, _cname, f(self))
        return getattr(self, _cname)
    return _inner

# The server is older than your desktop machine, so we add some extra to the mimetypes
mimetypes.add_type('application/x-msi', 'msi')
mimetypes.add_type('application/x-7z-compressed', '7z')
mimetypes.add_type('application/x-gimp-palette', '.gpl')

class MimeType(object):
    """Translate mime type to icons and do other useful conversions"""
    type_tr = {
        'application': {
            'document': ['pdf', 'rtf', 'word', 'powerpoint', 'excel',
                         'spreadsheet', 'text', 'presentation', 'chart'],
            'archive': ['bzip', 'zip', 'gzip', 'tar'],
            'text': ['xml', 'plain'],
            'code': ['c++', 'javascript'],
            'palette': ['gimp-palette'],
        },
        'text': {
            'document': ['rtf', 'html'],
            'code': ['python', 'perl', 'pascal', 'script', 'tcl', 'shell',
                     'c-header', 'c', 'c++', 'css', 'java'],
        }
    }
    s_tr = {
        'compress': 'zip', 'compressed': 'zip', 'bzip2': 'bzip', 'gtar': 'tar', 'gnutar': 'tar',
        'sh': 'shell', 'h': 'c-header', 'cplusplus': 'c++', 'java-source': 'java',
        'mspowerpoint': 'powerpoint', 'msexcel': 'excel', 'msword': 'word',
        'richtext': 'rtf',
    }

    def __init__(self, mime='application/unknown', filename=None):
        if filename:
            mime = mimetypes.guess_type(filename, True)[0] or mime
        (self.major, self.minor) = mime.split('/', 1)

    def __str__(self):
        return self.major + "/" + self.minor

    @cached
    def subtype(self):
        """Return the sub-type as a human readable thing"""
        value = self.minor.rsplit('+', 1)[0]
        for x in ('x-', 'script.', 'vnd.', 'ms-', 'windows-', 'oasis.opendocument.', 'microsoft.'):
            if value.startswith(x):
                value = value[len(x):]
        return self.s_tr.get(value, value)

    @cached
    def type(self):
        """Returns the type for this mime-type"""
        value = self.major
        for x, lin in self.type_tr.get(value, {}).items():
            if self.subtype() in lin:
                return x
        return value

    def is_text(self):
        """We test for both because javascript in code and html in document"""
        return self.type() in ['text', 'code'] or self.major == 'text'

    def is_xml(self):
        """Returns true if this mimetype is an xml document"""
        return self.minor.endswith('+xml') or self.minor == 'xml'

    def is_image(self):
        """Returns true if this mimetype is any sort of image"""
        return self.major == 'image'

    def is_raster(self):
        """Returns true if this mimetype is specific raster images"""
        return self.is_image() and self.minor in ['jpeg', 'gif', 'png']

    def icon(self, subdir=""):
        """Returns the icon for use in showing mimetypes"""
        for ft_icon in [self.subtype(), self.type(), self.minor, self.major, 'unknown']:
            filename = os.path.join(MIME_DIR, subdir, ft_icon+'.svg')
            if finders.find(filename):
                return static(filename)
        return self.static("unknown")

    @staticmethod
    def static(name):
        """Returns a static icon for this mimetype name"""
        return static('mime', name + '.svg')

    def banner(self):
        """Returns a banner image icon"""
        return self.icon('banner')

VIDEO_URLS = {
    'youtube': r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be'
               r'/)(watch\?v=|embed/|v/|.+\?v=)?(?P<video_id>[^&=%\?]{11})',
    'vimeo': r'(http:\/\/)?(www\.)?(vimeo\.com)(\/channels\/.+)?\/(?P<video_id>.+)/?',
}

def video_embed(url):
    """Embed the video using known video_urls"""
    if url is not None:
        for site_id, regex in VIDEO_URLS.items():
            match = re.match(regex, url)
            if match:
                return {'type': site_id, 'id': match.group('video_id')}
    return None

def hash_verify(sig_type, sig, data):
    """Verify the signature against the data (for example md5)"""
    import hashlib
    sig.file.open()
    sig.file.seek(0)
    digest = str(sig.file.read()).split(' ')[0].strip()
    hasher = getattr(hashlib, sig_type, hashlib.sha1)()
    for chunk in data.chunks():
        hasher.update(chunk)
    return hasher.hexdigest() == digest

def gpg_verify(user, sig, data):
    """
    You can not verify the same data file with two different signatures twice.
    """
    if sig.closed:
        if hasattr(sig, 'open'):
            sig.open()
        else:
            raise IOError("Can't verify on closed file handle.")

    import gnupg
    gpg = gnupg.GPG(homedir=os.path.join(settings.MEDIA_ROOT, 'gnupg'))
    gpg.import_keys(str(user.gpg_key))
    result = bool(gpg.verify_file(sig, data.path))
    del gpg
    return result


class FileEx(object):
    def __init__(self, file_or_path, mime=None):
        if mime is None:
            if os.path.isfile(file_or_path):
                mime = MimeType(filename=file_or_path)
            else:
                raise IOError("No Mime type specified.")
        self.mime = mime
        self.fop = file_or_path

    @property
    def file_handle(self):
        """Returns the raw file handle, filename -> file handle"""
        if not hasattr(self.fop, 'read'):
            if not os.path.isfile(self.fop):
                raise IOError("File not found %s\n" % str(self.fop))
            self.fop = open(self.fop, 'rb')
        if hasattr(self.fop, 'file'):
            self.fop = self.fop.file
        return self.fop

    def peek(self, t):
        ret = self.file_handle.read(t)
        self.file_handle.seek(0)
        return ret

    @property
    def content(self):
        """Returns the file handle with the right decoder (i.e. gzip)"""
        if self.peek(2) == '\x1f\x8b':
            return gzip.GzipFile(fileobj=self.file_handle)
        self.file_handle.seek(0)
        return self.file_handle

    def as_text(self, lines=None):
        """Return a file as text"""
        if self.mime.is_text() or self.mime.is_xml():
            # GZip magic number for svgz files.
            if lines is not None:
                return "".join(line.decode('utf-8') for line in self.content.readlines())
            return self.content.read().decode('utf-8')
        return "Not text!"

    @property
    def media_coords(self):
        """Returns height/width for images, lines/charicters for text"""
        if self.mime.is_raster():
            return get_image_dimensions(self.content)
        if self.mime.is_xml() and self.mime.is_image():
            return self._svg_coords()
        if self.mime.is_text():
            try:
                return self._text_coords()
            except UnicodeDecodeError:
                raise ValueError("Not a text file.")
        return (None, None)

    def _svg_coords(self):
        def coord(n):
            # XXX This should calculate the units correctly in future (i.e. mm -> px)
            return int(float(''.join(c for c in n if c in '.0123456789')))

        from xml.dom.minidom import parse, Node
        try:
            doc = parse(self.content).documentElement
            return (coord(doc.getAttribute('width')),
                    coord(doc.getAttribute('height')))
        except:
            return (-1,-1)

    def _text_coords(self):
        num_lines = 0
        num_words = 0
        num_chars = 0
        content = self.content
        for line in content.readlines():
            words = line.split()
            num_lines += 1
            num_words += len(words)
            num_chars += len(line)
        return (num_lines, num_words)

