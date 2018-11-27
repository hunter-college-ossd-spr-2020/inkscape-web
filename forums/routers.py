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
Route forums to use xapian index instead.
"""

from haystack.routers import BaseRouter

from .search_indexes import TopicIndex, CommentIndex
from .models import ForumTopic, Comment

class ForumRouter(BaseRouter):
    """
    Route searching and indexing for forums
    """
    @staticmethod
    def for_read(models=(), **_):
        """Forum searches should go to forums haystack"""
        if Comment in models or ForumTopic in models:
            return 'forums'
        return 'default'

    @staticmethod
    def for_write(index=None, instance=None, **_):
        """Return forums haystack when indexing forums"""
        if isinstance(index, (TopicIndex, CommentIndex)):
            return 'forums'
        if isinstance(instance, (ForumTopic, Comment)):
            return 'forums'
        return 'default'
