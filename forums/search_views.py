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
# pylint: disable=too-many-ancestors
"""
Forum views, show topics, comments and link to apps.
"""

from haystack.forms import SearchForm
from haystack.query import SearchQuerySet
from haystack.views import SearchView as SearchBase

from .models import Comment, ForumTopic

class ForumSearch(SearchBase):
    """Generic form search"""
    form_class = SearchForm
    results_per_page = 10

    @property
    def model(self):
        """Provide a model to search"""
        raise NotImplementedError("Please provide a model to search")

    def __init__(self, *args, **kwargs):
        """Overwrite some important aspects of the search base"""
        kwargs['searchqueryset'] = SearchQuerySet(using='forums').models(self.model)
        kwargs['form_class'] = self.form_class
        super().__init__(*args, **kwargs)

    def get_context(self):
        data = super().get_context()
        data['search_name'] = type(self).__name__
        return data

class TopicSearchForm(SearchForm):
    """Search only the topic's subject line"""
    def search(self):
        if not self.is_valid():
            return self.no_query_found()
        if not self.cleaned_data.get('q'):
            return self.no_query_found()

        return self.searchqueryset.auto_query(
            self.cleaned_data['q'], fieldname='subject').load_all()

class CommentSearch(ForumSearch):
    """Restrict the search to the selected language only"""
    template = "forums/comment_search.html"
    form_class = SearchForm
    model = Comment

class TopicSearch(ForumSearch):
    """Restrict the search to the selected language only"""
    template = "forums/topic_search.html"
    form_class = SearchForm
    model = ForumTopic

class TopicSubjectSearch(TopicSearch):
    """Search only the topic's subject line"""
    form_class = TopicSearchForm
