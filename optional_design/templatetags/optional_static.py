#
# Copyright 2018, Martin Owens <doctormo@gmail.com>
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
Provide a link into the optional_design static library.
"""

import os

from django import template
from django.templatetags.static import StaticNode

from .. import get_design

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

register = template.Library() # pylint: disable=invalid-name

class OptionalStaticNode(StaticNode):
    """Provide a replacement optional static node interface"""
    def url(self, context):
        design = get_design()
        if design is None:
            raise ValueError("Not using an optional design in request.")
        path = self.path.resolve(context)
        location = os.path.join(STATIC_DIR, design, path)
        # If the file doesn't exist, we don't load it.
        if os.path.isfile(location):
            return self.handle_simple(os.path.join(design, path))
        return self.handle_simple(path)

@register.tag('static')
def do_static(parser, token):
    """Provide a replacement static template tag"""
    return OptionalStaticNode.handle_token(parser, token)
