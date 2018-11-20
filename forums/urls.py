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
Forum views accessable from the website.
"""

from django.conf.urls import url
from inkscape.url_utils import url_tree

from .views import (
    ForumList, TopicList, AddTopic, TopicDetail, TopicSearch,
    CommentEdit, CommentSearch, CommentEmote,
)

urlpatterns = [ # pylint: disable=invalid-name
    url(r'^$', ForumList.as_view(), name="list"),
    url(r'^search/$', TopicSearch(), name='search'),
    url(r'^search/posts/$', CommentSearch(), name='search.posts'),
    url_tree(
        r'^c(?P<pk>\d+)/',
        url(r'^emote/$', CommentEmote.as_view(), name='emote'),
        url(r'^edit/$', CommentEdit.as_view(), name='comment_edit'),
        #url(r'^del/$', CommentDelete.as_view(), name='comment_delete'),
    ),
    url_tree(
        r'^(?P<slug>[\w-]+)/',
        url(r'^$', TopicList.as_view(), name='detail'),
        url(r'^new/$', AddTopic.as_view(), name='create'),
    ),
    url_tree(
        r'^(?P<forum>[\w-]+)/(?P<slug>[\w-]+)/',
        url(r'^$', TopicDetail.as_view(), name='topic'),
    ),
]
