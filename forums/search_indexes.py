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
Index the comments/forum system to find interesting things.
"""

from haystack.indexes import (
    SearchIndex, Indexable, CharField, DateTimeField, IntegerField,
)

from .models import ForumTopic, Comment
from .templatetags.forum_comments import FORUM_PREFETCH, FORUM_DEFER

class TopicIndex(SearchIndex, Indexable):
    """
    Index of the topics
    """
    text = CharField(document=True, use_template=True)
    last_posted = DateTimeField(stored=True, model_attr='last_posted')
    subject = CharField(stored=True, model_attr='subject', indexed=True)

    def get_model(self):
        return ForumTopic

    def get_updated_field(self):
        return 'last_posted'

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.none()

class CommentIndex(SearchIndex, Indexable):
    """
    Index the comment objects
    """
    text = CharField(document=True, model_attr='comment')
    user_id = IntegerField(stored=True, model_attr='user_id', null=True)
    submit_date = DateTimeField(stored=True, model_attr='submit_date')

    def get_model(self):
        return Comment

    def get_updated_field(self):
        return 'submit_date'

    def read_queryset(self, using=None):
        return self.get_model().objects.prefetch_related(*FORUM_PREFETCH).defer(*FORUM_DEFER)

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(is_removed=False, is_public=True).filter(pk=1906)
