#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
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
Provide useful tools for showing svg file in the templates directly.
"""

import os

from xml.dom.minidom import parseString
from django.template import Library

from django.template.defaultfilters import filesizeformat

register = Library() # pylint: disable=invalid-name

@register.filter("filefieldsize")
def filefieldsize(field):
    if field and os.path.isfile(field.path):
        filesizeformat(field.size)
    return ''

def coord(num):
    """Turns a string (from svg) into an integer"""
    return int(float(''.join(c for c in num if c in '.0123456789')))

@register.filter("svg_size")
def svg_size(text, args):
    """Returns the document's bounding box size in px"""
    (width, height) = args.split('|', 1)
    try:
        index_of = text.index("<svg")
        until = text.index(">", index_of)
    except ValueError as error:
        return "<h1>ValueError from svg tag parse: %s</h1>" % str(error)

    tag = text[index_of:until+1] + "</svg>"
    try:
        doc = parseString(tag).documentElement
        if not doc.getAttribute('viewBox'):
            vb_width = coord(doc.getAttribute('width'))
            vb_height = coord(doc.getAttribute('height'))
            doc.setAttribute('viewBox', "0 0 %d %d" % (vb_width, vb_height))
        doc.setAttribute('height', height)
        doc.setAttribute('width', width)
        return text[:index_of] + doc.toxml()[:-2] + text[until:]
    except (ValueError, KeyError, AttributeError) as error:
        return "<h1>ERROR: %s</h1>" % str(error)
