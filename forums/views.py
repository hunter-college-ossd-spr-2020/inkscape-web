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

from django.views.generic import (
    ListView, DetailView, FormView, TemplateView, UpdateView, DeleteView
)
from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404

from django_comments.models import CommentFlag

from .base_views import FieldUpdateView
from .forms import NewTopicForm, EditCommentForm, AddCommentForm
from .mixins import (
    CsrfExempt, UserVisit, UserRequired, OwnerRequired, ModeratorRequired, ForumMixin
)
from .models import Comment, Forum, ForumTopic, ModerationLog
from .templatetags.forum_comments import FORUM_PREFETCH, FORUM_DEFER

class ForumList(UserVisit, ForumMixin, TemplateView):
    """A list of all available forums"""
    template_name = 'forums/forum_list.html'

class ModerationList(ListView):
    """A list of all moderation actions logged"""
    model = ModerationLog
    paginate_by = 20

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

class CommentCreate(UserRequired, FormView):
    """
    Create a new comment.
    """
    model = Comment
    title = _('New Comment')
    form_class = AddCommentForm
    template_name = "forums/comment_form.html"

    def get_parent(self):
        """Return the parent, i.e. the topic object"""
        topic = ForumTopic.objects.get(slug=self.kwargs['slug'])
        return topic.comment_subject

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'user': self.request.user,
            'ip_address': self.request.META.get("REMOTE_ADDR", None),
            'target_object': self.get_parent(),
        })
        return kwargs

    def form_valid(self, form):
        obj = form.save()
        topic = self.get_parent()
        url = topic.get_absolute_url() + '#c' + str(obj.pk)
        return HttpResponseRedirect(url)

class CommentEdit(OwnerRequired, UpdateView):
    """
    Edit comment in place.
    """
    model = Comment
    title = _('Edit Comment')
    form_class = EditCommentForm
    template_name = "forums/comment_form.html"

    def log_details(self):
        return {'diff': 'TBD'}

class CommentModPublic(ModeratorRequired, FieldUpdateView):
    """
    Toggle the public flag of a comment, this can also hide.
    """
    model = Comment
    field = 'is_public'
    value = '!'

    def field_changed(self, obj, is_public): # pylint: disable=arguments-differ
        """Enable the user for posting if they are approved"""
        if obj.user and is_public:
            comments = Comment.objects.filter(user_id=obj.user.pk, is_public=True, is_removed=False)
            if comments.count() >= 2:
                self.add_permissions(obj.user)
        self.sync_topic(obj, obj.get_topic())
        return super().field_changed(obj, is_public=is_public)

    @staticmethod
    def sync_topic(comment, topic):
        """Makes sure comment and topic status are in-sync"""
        if topic and comment == topic.comments.first():
            topic.locked = not comment.is_public
            topic.save()

    @staticmethod
    def add_permissions(user):
        """Add permission to post to the forums"""
        permissions = Permission.objects.filter(content_type__model='forumtopic')
        comment = permissions.get(codename='can_post_comment')
        user.user_permissions.add(comment)
        topic = permissions.get(codename='can_post_topic')
        user.user_permissions.add(topic)


class CommentModRemove(ModeratorRequired, FieldUpdateView):
    """
    Toggle the removal of comments, this can also un-remove.
    """
    model = Comment
    field = 'is_removed'
    value = '!'

class CommentModList(ModeratorRequired, ForumMixin, ListView):
    """
    List all comnments which are not yet published
    """
    template_name = "forums/forumcomment_list.html"

    def get_queryset(self):
        return Comment.objects\
            .filter(is_public=False, is_removed=False)\
            .prefetch_related(*FORUM_PREFETCH).defer(*FORUM_DEFER)

class TopicMixin(object):
    template_name = "forums/moderator_form.html"
    model = ForumTopic

class TopicMove(ModeratorRequired, TopicMixin, UpdateView):
    title = _('Move Topic')
    fields = ('forum',)

    def log_details(self):
        """Return the old and new forums"""
        obj = self.get_object()
        return {'from_forum': obj.forum.slug}

class TopicEdit(ModeratorRequired, TopicMixin, UpdateView):
    title = _('Edit Topic')
    fields = ('subject', 'sticky', 'locked')

class TopicDelete(ModeratorRequired, TopicMixin, DeleteView):
    title = _('Delete Topic')

    def get_success_url(self):
        self.record_action()
        return self.object.forum.get_absolute_url()

    def log_details(self):
        obj = self.get_object()
        return {'subject': obj.subject}

class TopicCreate(UserRequired, FormView):
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

class CommentEmote(CsrfExempt, UserRequired, UpdateView):
    """Update an Emote on a comment using a comment flag"""
    model = CommentFlag
    fields = ('flag',)

    def form_valid(self, form):
        """Redirect OR return Empty 200 SUCESS"""
        self.object = form.save()
        url = self.request.POST.get('next', self.request.GET.get('next', None))
        if url:
            HttpResponseRedirect(url)
        return JsonResponse({
            'id': self.object.pk,
            'flag': self.object.flag,
            'comment': self.object.comment_id,
            'user': self.object.user_id,
        })

    def get_object(self, queryset=None):
        return self.get_queryset().get_or_create(user=self.request.user,
                                                 comment_id=self.kwargs['pk'])[0]
