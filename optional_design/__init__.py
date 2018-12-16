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
Provide a middleware to identify when the request is an optional
design request and saves the right information.
"""

import threading

from django import urls
from django.utils import six
from django.utils.functional import lazy

LOCAL = threading.local()

def get_design():
    return getattr(LOCAL, 'optional_design', None)

def set_design(design):
    LOCAL.optional_design = design

old_reverse = urls.reverse # pylint: disable=invalid-name

def new_reverse(*args, **kwargs):
    """Add the design to any design being loaded"""
    url = old_reverse(*args, **kwargs)
    design = get_design()
    if design is not None:
        if '?' in url:
            url += '&od={}'.format(design)
        else:
            url += '?od={}'.format(design)
    return url

urls.reverse = new_reverse
urls.lazy_reverse = lazy(new_reverse, six.text_type)
