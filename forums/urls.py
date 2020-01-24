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

from django.conf.urls import include, url
from inkscape.url_utils import url_tree
from person import user_urls

from .views import (
    ModerationList, ForumList,
    TopicList, TopicDetail, TopicCreate, TopicMove, TopicEdit, TopicDelete,
    TopicMerge, TopicSplit, UserTopicList, UnreadTopicList,
    CommentList, CommentCreate, CommentEdit, CommentEmote, Subscriptions,
    CommentModList, CommentModPublic, CommentModRemove,
    UserFlagList, UserModList, UserBanList, WordBanList,
    UserFlagToggle, UserModToggle, UserBanToggle, WordFlagCreate, WordFlagDelete,
)
from .rss import ForumTopicFeed

from .search_views import CommentSearch, TopicSearch, TopicSubjectSearch

user_urls.urlpatterns += [
    url(r'^comments/$', CommentList.as_view(), name="comment_list"),
    url(r'^topics/$', UserTopicList.as_view(), name="topic_list"),
    url(r'^topics/rss/$', ForumTopicFeed(), name='topic_feed'),
]

urlpatterns = [ # pylint: disable=invalid-name
    url(r'^$', ForumList.as_view(), name="list"),
    url(r'^log/$', ModerationList.as_view(), name="log"),
    url_tree(
        r'^users/',
        url(r'^banned/$', UserBanList.as_view(), name='ban_list'),
        url(r'^words/$', WordBanList.as_view(), name='word_list'),
        url(r'^mods/$', UserModList.as_view(), name='mod_list'),
        url(r'^flags/$', UserFlagList.as_view(), name='flag_list'),
        url(r'^banned/flag/$', UserBanToggle.as_view(), name='ban_user'),
        url(r'^mods/flag/$', UserModToggle.as_view(), name='mod_user'),
        url(r'^flags/flag/$', UserFlagToggle.as_view(), name='flag_user'),
        url(r'^words/create/$', WordFlagCreate.as_view(), name='create_words'),
        url(r'^words/delete/(?P<pk>\d+)/$', WordFlagDelete.as_view(), name='delete_words'),
    ),
    url(r'^unread/$', UnreadTopicList.as_view(), name="unread"),
    url(r'^check/$', CommentModList.as_view(), name="check"),
    url(r'^search/$', TopicSubjectSearch(), name='search'),
    url(r'^search/topics/$', TopicSearch(), name='search.topics'),
    url(r'^search/posts/$', CommentSearch(), name='search.posts'),
    url(r'^topics/$', TopicList.as_view(), name="topic_list"),
    url(r'^subscriptions/$', Subscriptions.as_view(), name="topic_subs"),
    url(r'^phpbb/', include('forums.plugins.phpbb.urls', namespace='phpbb')),
    url(r'^~(?P<username>[^\/]+)/rss/$', ForumTopicFeed(), name='topic_feed'),
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
        url(r'^rss/$', ForumTopicFeed(), name='topic_feed'),
        url(r'^new/$', TopicCreate.as_view(), name='create'),
        url(r'^move/$', TopicMove.as_view(), name='topic_move'),
        url(r'^edit/$', TopicEdit.as_view(), name='topic_edit'),
        url(r'^del/$', TopicDelete.as_view(), name='topic_delete'),
        url(r'^merge/$', TopicMerge.as_view(), name='topic_merge'),
        url(r'^split/$', TopicSplit.as_view(), name='topic_split'),
    ),
    url_tree(
        r'^(?P<forum>[\w-]+)/(?P<slug>[\w-]+)/',
        url(r'^$', TopicDetail.as_view(), name='topic'),
        url(r'^comment/$', CommentCreate.as_view(), name='comment_create'),
    ),
]
