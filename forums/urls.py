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
from person import user_urls

from .views import (
    ModerationList, ForumList,
    TopicList, TopicDetail, TopicCreate, TopicMove, TopicEdit, TopicDelete,
    CommentList, CommentCreate, CommentEdit, CommentEmote,
    CommentModList, CommentModPublic, CommentModRemove,
    UserBanList, UserBan
)

from .search_views import CommentSearch, TopicSearch, TopicSubjectSearch

user_urls.urlpatterns += [
    url(r'^comments/$', CommentList.as_view(), name="comment_list"),
    url(r'^topics/$', TopicList.as_view(), name="topic_list"),
    url(r'^ban/$', UserBan.as_view(), name='ban_user'),
]

urlpatterns = [ # pylint: disable=invalid-name
    url(r'^$', ForumList.as_view(), name="list"),
    url(r'^log/$', ModerationList.as_view(), name="log"),
    url(r'^ban/$', UserBanList.as_view(), name='ban_list'),
    url(r'^check/$', CommentModList.as_view(), name="check"),
    url(r'^search/$', TopicSubjectSearch(), name='search'),
    url(r'^search/topics/$', TopicSearch(), name='search.topics'),
    url(r'^search/posts/$', CommentSearch(), name='search.posts'),
    url(r'^topics/$', TopicList.as_view(), name="topic_list"),
    url_tree(
        r'^c(?P<pk>\d+)/',
        url(r'^emote/$', CommentEmote.as_view(), name='emote'),
        url(r'^edit/$', CommentEdit.as_view(), name='comment_edit'),
        url(r'^rem/$', CommentModRemove.as_view(), name='comment_remove'),
        url(r'^pub/$', CommentModPublic.as_view(), name='comment_public'),
    ),
    url_tree(
        r'^(?P<slug>[\w-]+)/',
        url(r'^$', TopicList.as_view(), name='topic_list'),
        url(r'^new/$', TopicCreate.as_view(), name='create'),
        url(r'^move/$', TopicMove.as_view(), name='topic_move'),
        url(r'^edit/$', TopicEdit.as_view(), name='topic_edit'),
        url(r'^del/$', TopicDelete.as_view(), name='topic_delete'),
    ),
    url_tree(
        r'^(?P<forum>[\w-]+)/(?P<slug>[\w-]+)/',
        url(r'^$', TopicDetail.as_view(), name='topic'),
        url(r'^comment/$', CommentCreate.as_view(), name='comment_create'),
    ),
]
