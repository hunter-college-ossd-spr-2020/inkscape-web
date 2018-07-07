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
Inkscape page manipulation
"""
from django.core.paginator import Paginator, Page

class InkscapePaginator(Paginator):
    """Add some extra paginator functionality"""
    def _get_page(self, *args, **kwargs):
        return InkscapePage(*args, **kwargs)

class InkscapePage(Page): # pylint: disable=too-many-ancestors
    """The page portion of the paginator"""
    hide_range = 4

    @property
    def page_range(self):
        """Return a compressed range"""
        start = self.number - self.hide_range
        stop = self.number + self.hide_range - 1
        count = self.paginator.count
        if start < 0:
            start = 0
            if stop < count:
                stop += abs(start)
        if stop > count:
            stop = count
            if start > 0 + abs(count - stop):
                start -= abs(count - stop)

        if start > 0:
            yield 1
            yield None
        for page in self.paginator.page_range[start:stop]:
            yield page
        if stop < count:
            yield None
            yield count
