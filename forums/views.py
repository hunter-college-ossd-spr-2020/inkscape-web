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

from django.views.generic import ListView, DetailView, FormView
from django.http import Http404
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator

from django_comments.models import Comment

from .forms import NewTopicForm
from .mixins import UserRequired
from .models import Q, ForumGroup, Forum, ForumTopic

class ForumList(UserRequired, ListView):
    """A list of all available forums"""
    cache_tracks = [ForumGroup, ForumTopic, Comment]
    paginate_by = 12

    def get_queryset(self):
        language = translation.get_language()
        return Forum.objects.filter(Q(lang=language) | Q(lang=''))

class TopicList(UserRequired, ListView):
    """A list of all topics in a forum"""
    paginate_by = 20

    def get_queryset(self):
        self.forum = Forum.objects.get(slug=self.kwargs['slug'])
        return self.forum.topics.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.forum
        return context

class TopicDetail(UserRequired, DetailView):
    """A single topic view"""
    def get_queryset(self):
        return ForumTopic.objects.filter(forum__slug=self.kwargs['forum'])

class AddTopic(UserRequired, FormView):
    """
    Topics can be made manually like this, or auto
       generated when attached to a content type
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
        topic = form.save()
        self.success_url = topic.get_absolute_url()
        return super().form_valid(form)
