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

import os
import mimetypes

from pygments import highlight, lexers, formatters
from pygments.util import ClassNotFound

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
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

RATIOS = {
    1.0: ('square', _('Square')),
    1.414: ('iso216', _('ISO Paper (Landscape)'), _('ISO Paper (Portrait)')),
    1.618: ('golden', _('Golden Ratio (Landscape)'), _('Golden Ratio (Portrait)')),
    11 / 8.5: ('us-letter', _('US Letter (Landscape)'), _('US Letter (Portrait)')),
    4 / 3.0: ('video', _('Standard Definition 4:3'), _('Unusual Definition 3:4')),
    16 / 9.0: ('widescreen', _('Widescreen 16:9'), _('Tallscreen 9:16')),
    21 / 9.0: ('ultrawide', _('Ultra-Widescreen 21:9'), _('Ultra-Tallscreen 9:21')),
    32 / 9.0: ('superwide', _('Super-Widescreen 32:9'), _('Super-Tallscreen 9:32')),
    16 / 10.0: ('wxga', _('Widescreen Display 16:10'), _('Rotated Widescreen Display 10:16')),
    3 / 2.0: ('35mm', _('35mm Film'), _('Rotated 35mm Film')),
    5 / 3.0: ('16mm', _('16mm Film'), _('Rotated 16mm Film')),
}

def get_aspect(width, height, err=0.02):
    """
    Attempt to identify an aspect ration (returns None if none matched)

    Returns (aspect_radio, id_name, label) if found.
    """
    try:
        arr = [float(width), float(height)]
        asp = max(arr) / min(arr)
        for otr in RATIOS:
            if otr - err <= asp <= otr + err:
                port = -2 if arr[0] > arr[1] else -1
                return (otr, RATIOS[otr][0], RATIOS[otr][port])
    except ValueError:
        pass
    return None

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

def hash_verify(sig_type, sig, data):
    """Verify the signature against the data (for example md5)"""
    import hashlib
    sig.file.open()
    sig.file.seek(0)
    digest = sig.file.read().split(b' ')[0].strip().decode('ascii')
    hasher = getattr(hashlib, sig_type, hashlib.sha1)()
    for chunk in data.chunks():
        hasher.update(chunk)
    return hasher.hexdigest() == digest

def gpg_verify(user, sig, data):
    """
    You can not verify the same data file with two different signatures twice.
    """
    import gnupg

    if sig.closed:
        if hasattr(sig, 'open'):
            sig.open()
        else:
            raise IOError("Can't verify on closed file handle.")

    with open(os.path.join(settings.LOGBOOK_ROOT, 'gnupg.log'), 'a') as log:
        log.write("\n=======\n")
        log.write(f"Verifying signature for file: {data.path} ({user.username})\n")
        # This is python-gnupg and NOT gnupg, make sure you have the right one installed
        gpg = gnupg.GPG(gnupghome=os.path.join(settings.MEDIA_ROOT, 'gnupg'))
        ret = gpg.import_keys(str(user.gpg_key))
        log.write(f"Import User Key: {ret.stderr}") # pylint: disable=no-member
        result = gpg.verify_file(sig, data.path)
        log.write(f"Verify Sig: {result.stderr}") # pylint: disable=no-member
    del gpg
    return bool(result)


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

class RemoteError(IOError):
    """Remote server didn't respond as expected"""

def url_filefield(url, filename=None):
    """
    Download the given url and return it as a file field
    """
    if not url:
        return None
    from django.core import files
    from io import BytesIO
    import requests
    resp = requests.get(url)
    if resp.status_code != 200:
        if resp.status_code == 404:
            raise RemoteError("File Not Found")
        raise RemoteError("Server Error")
    bhl = BytesIO()
    bhl.write(resp.content)
    if filename is None:
        filename = url.split("/")[-1]
    return files.File(bhl, filename)
