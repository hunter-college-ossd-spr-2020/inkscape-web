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

from django.views.generic import ListView, DetailView, FormView, TemplateView, UpdateView
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from haystack.forms import SearchForm
from haystack.query import SearchQuerySet
from haystack.views import SearchView as SearchBase

from django_comments.models import CommentFlag

from .forms import NewTopicForm, EditCommentForm
from .mixins import UserVisit, UserRequired, OwnerRequired, ForumMixin
from .models import Comment, Forum, ForumTopic

class ForumList(UserVisit, ForumMixin, TemplateView):
    """A list of all available forums"""
    template_name = 'forums/forum_list.html'


class TopicList(UserVisit, ForumMixin, ListView):
    """A list of all topics in a forum"""
    paginate_by = 20

    def get_queryset(self):
        self.forum = Forum.objects.get(slug=self.kwargs['slug'])
        return self.forum.topics.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forum'] = self.forum
        return context

class TopicDetail(UserVisit, DetailView):
    """A single topic view"""
    def get_queryset(self):
        return ForumTopic.objects\
            .filter(forum__slug=self.kwargs['forum'])\
            .select_related('forum', 'forum__group')

class CommentEdit(OwnerRequired, UpdateView):
    """
    Edit comment in place.
    """
    model = Comment
    title = _('Edit Comment')
    form_class = EditCommentForm
    template_name = "forums/comment_form.html"

class AddTopic(UserRequired, FormView):
    """
    Add a topic manually to the forum creating topics and comments.
    """
    title = _("Create a new Forum Topic")
    template_name = "forums/forumtopic_form.html"
    form_class = NewTopicForm

    def get_parent(self):
        """Return the parent of the topic, i.e. the forum"""
        return get_object_or_404(Forum, slug=self.kwargs['slug'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'user': self.request.user,
            'ip_address': self.request.META.get("REMOTE_ADDR", None),
            'target_object': self.get_parent(),
        })
        if kwargs['target_object'].content_type:
            raise Http404("Topics are not allowed to be created.")
        return kwargs

    def form_valid(self, form):
        return HttpResponseRedirect(form.save().get_absolute_url())

class CommentSearch(SearchBase):
    """Restrict the search to the selected language only"""
    template = "forums/comment_search.html"
    results_per_page = 10
    form_class = SearchForm

    def __init__(self, *args, **kwargs):
        kwargs['searchqueryset'] = SearchQuerySet().models(Comment)
        super().__init__(*args, **kwargs)

class TopicSearch(SearchBase):
    """Restrict the search to the selected language only"""
    template = "forums/topic_search.html"
    results_per_page = 10
    form_class = SearchForm

    def __init__(self, *args, **kwargs):
        kwargs['searchqueryset'] = SearchQuerySet().models(ForumTopic)
        super().__init__(*args, **kwargs)


class CommentEmote(UserRequired, UpdateView):
    """Update an Emote on a comment using a comment flag"""
    model = CommentFlag
    fields = ('flag',)

    def form_valid(self, form):
        """Redirect OR return Empty 200 SUCESS"""
        self.object = form.save()
        url = self.request.POST.get('next', self.request.GET.get('next', None))
        if url:
            HttpResponseRedirect(url)
        return HttpResponse('')

    def get_object(self, queryset=None):
        return self.get_queryset().get_or_create(user=self.request.user,
                                                 comment_id=self.kwargs['pk'])[0]
