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

from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.views.generic import (
    ListView, DetailView, FormView, TemplateView, UpdateView, DeleteView
)
from django.contrib.auth import get_user_model
from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

from django_comments.models import CommentFlag

from .base_views import FlagCreateView, FieldUpdateView
from .forms import (
    NewTopicForm, EditCommentForm, AddCommentForm,
    SplitTopic, MergeTopics,
    CommentFlagForm,
)
from .mixins import (
    CsrfExempt, UserVisit, ForumMixin, TopicMixin,
    UserRequired, OwnerRequired, ModeratorRequired, ProgressiveContext
)
from .models import Comment, Forum, ForumTopic, ModerationLog, UserFlag
from .templatetags.forum_comments import FORUM_PREFETCH, FORUM_DEFER

class ForumList(UserVisit, ForumMixin, TemplateView):
    """A list of all available forums"""
    template_name = 'forums/forum_list.html'

    def get_context_data(self, **kwargs):
        """Pick up some extra content for the front page"""
        data = super().get_context_data(**kwargs)
        data['recent_topics'] = ForumTopic.objects\
                .filter(locked=False, removed=False)\
                .for_user(self.request.user)\
                .select_related('forum')\
                .order_by('-first_posted')[:10]
        return data

class ModerationList(ModeratorRequired, ListView):
    """A list of all moderation actions logged"""
    model = ModerationLog
    paginate_by = 20
    ordering = ('-performed',)

class TopicList(UserVisit, ForumMixin, ListView):
    """A list of all topics in a forum"""
    model = ForumTopic
    paginate_by = 20

    def get_ordering(self):
        if 'slug' in self.kwargs:
            return ('-sticky', '-last_posted',)
        return ('-last_posted',)

    def get_queryset(self):
        qset = super().get_queryset().select_related('forum')
        self.set_context_datum('topic_list', True)
        qset = qset.for_user(self.request.user).filter(removed=False)
        if 'count' in self.request.GET:
            try:
                qset = qset.filter(post_count=int(self.request.GET['count']))
            except ValueError:
                pass
        if 'slug' in self.kwargs:
            forum = get_object_or_404(Forum, slug=self.kwargs['slug'])
            qset = qset.filter(forum_id=forum.pk)
            self.set_context_datum('forum', forum)
        if 'username' in self.kwargs:
            user = get_object_or_404(get_user_model(), username=self.kwargs['username'])
            qset = qset.filter(first_username=self.kwargs['username'])
            self.set_context_datum('forum_user', user)
        if self.request.user.is_authenticated():
            qset.set_user(self.request.user)
        if self.kwargs:
            self.set_context_datum('rss', reverse("forums:topic_feed", kwargs=self.kwargs))
        return qset

class UserTopicList(TopicList):
    """A list of topics that the user has posted themselves"""
    template_name = 'forums/forumtopic_list_user.html'

class Subscriptions(UserRequired, TopicList):
    """A list of subscribed threads"""
    template_name = 'forums/forumtopic_list_user.html'
    def get_queryset(self):
        qset = super().get_queryset()
        qset.set_user(self.request.user)
        self.set_context_datum('forum_user', self.request.user)
        return qset.subscribed_only()

class UnreadTopicList(TopicList):
    """An empty forum which javascript asks for the latest topics."""
    template_name = 'forums/forumtopic_list_unread.html'
    paginate_by = None

    def get_queryset(self):
        qset = super().get_queryset()
        return qset[:100]

class TopicDetail(UserVisit, DetailView):
    """A single topic view"""
    def dispatch(self, request, *args, **kwargs):
        """Catch jump to request"""
        ret = super().dispatch(request, *args, **kwargs)
        jumpto = request.GET.get('jumpto', None)
        if jumpto:
            try:
                dtime = datetime.strptime(jumpto, "%Y-%m-%dT%H:%M:%S.%fZ")
                tzone = timedelta(minutes=int(request.GET.get('tz', 0)))
                dtime += tzone
                dtime = make_aware(dtime, None) # Assumes server is UTC!
                topic = self.get_object()
                comment = topic.comments.filter(submit_date__gt=dtime).first()
                if comment:
                    url = topic.get_absolute_url()
                    return HttpResponseRedirect('{}#c{}'.format(url, comment.pk))
            except ValueError as err:
                print("ERROR: {}".format(err))
        return ret

    def get_queryset(self):
        return ForumTopic.objects\
            .filter(forum__slug=self.kwargs['forum'])\
            .select_related('forum', 'forum__group')

class CommentList(UserVisit, ForumMixin, ListView):
    """List comments, all of them or for a specific user"""
    model = Comment
    paginate_by = 20

    @property
    def template_name(self):
        if self.request.user.is_authenticated:
            if self.request.user.username == self.kwargs['username']:
                return 'forums/comment_list_user.html'
        return 'forums/comment_list.html'

    def get_queryset(self):
        qset = super().get_queryset()
        if 'username' in self.kwargs:
            user = get_user_model().objects.get(username=self.kwargs['username'])
            qset = qset.filter(user_id=user.pk)
            self.set_context_datum('forum_user', user)
        return qset.order_by('-submit_date')


class CommentCreate(UserRequired, FormView):
    """
    Create a new comment.
    """
    model = Comment
    form_class = AddCommentForm
    template_name = "forums/comment_form.html"
    context_title = _('New Comment')

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
        url = "{0}?c={1}#c{1}".format(topic.get_absolute_url(), obj.pk)
        return HttpResponseRedirect(url)

class CommentEdit(OwnerRequired, UpdateView):
    """Edit comment in place."""
    model = Comment
    form_class = EditCommentForm
    template_name = "forums/comment_form.html"
    context_title = _('Edit Comment')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        obj = form.save()
        return HttpResponseRedirect(obj.get_absolute_url())

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
        self.record_action(instance=obj, field=self.field, value=is_public)
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

    def field_changed(self, obj, is_removed): # pylint: disable=arguments-differ
        """Record the removal action in the moderators log"""
        self.record_action(instance=obj, field=self.field, value=is_removed)

class CommentModList(ModeratorRequired, ForumMixin, ListView):
    """
    List all comnments which are not yet published
    """
    template_name = "forums/moderator_list.html"

    def get_queryset(self):
        return Comment.objects\
            .filter(is_public=False, is_removed=False)\
            .prefetch_related(*FORUM_PREFETCH).defer(*FORUM_DEFER)


class TopicMove(ModeratorRequired, TopicMixin, UpdateView):
    """Allow a moderator to move a topic between forums"""
    context_title = _('Move Topic')
    fields = ('forum',)

    def log_details(self, **data):
        """Return the old and new forums"""
        return {'from_forum': self.get_object().forum.slug}

class TopicEdit(ModeratorRequired, TopicMixin, UpdateView):
    """Allow a topic to be edited by a moderator (or owner)"""
    context_title = _('Edit Topic')
    fields = ('subject', 'sticky', 'locked')

class TopicDelete(ModeratorRequired, TopicMixin, DeleteView):
    """Allow a topic to be deleted by a moderator"""
    context_title = _('Delete Topic')

    def get_success_url(self):
        self.record_action(subject=self.object.subject)
        return self.object.forum.get_absolute_url()

class TopicCreate(UserRequired, FormView):
    """
    Add a topic manually to the forum creating topics and comments.
    """
    context_title = _("Create a new Forum Topic")
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

class TopicMerge(ModeratorRequired, ProgressiveContext, FormView):
    """Allow moderators to merge two topics together"""
    template_name = "forums/moderator_form.html"
    form_class = MergeTopics
    context_title = _('Merge Topic')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['from_topic'] = get_object_or_404(ForumTopic, slug=self.kwargs['slug'])
        return kwargs

    def form_valid(self, form):
        return HttpResponseRedirect(form.save().get_absolute_url())

class TopicSplit(TopicMerge):
    """Allow moderators to split a topic in half"""
    form_class = SplitTopic
    context_title = _('Split Topic')


class CommentEmote(CsrfExempt, UserRequired, UpdateView):
    """Update an Emote on a comment using a comment flag"""
    model = CommentFlag
    form_class = CommentFlagForm

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
        qset = self.get_queryset().exclude(flag__in=self.form_class.reserved_flags)
        return qset.get_or_create(
            user=self.request.user,
            comment_id=self.kwargs['pk'],
        )[0]

class UserFlagBase(ModeratorRequired, ListView):
    """List of user flags (all kinds)"""
    model = UserFlag
    paginate_by = 10

    def get_queryset(self):
        return super().get_queryset().select_related('user').order_by('-created')

class UserFlagList(UserFlagBase):
    """Generate a list of user custom flags"""
    def get_queryset(self):
        return super().get_queryset().custom_flags()

class UserModList(UserFlagBase):
    """List of moderators"""
    template_name = 'forums/userflag_mod_list.html'

    def get_queryset(self):
        return super().get_queryset().moderators()\
            .prefetch_related('user__forum_moderation_actions')

class UserBanList(UserFlagBase):
    """List of banned users"""
    template_name = 'forums/userflag_ban_list.html'

    def get_queryset(self):
        return super().get_queryset().banned()

class UserFlagToggle(ModeratorRequired, FlagCreateView):
    """Toggle banning a user"""
    slug_field = 'username'
    model = get_user_model()
    field = 'forum_flags'

    @property
    def filters(self):
        return {'flag': self.get_flag()}

    def get_object(self):
        """Accept slug or GET"""
        self.kwargs['slug'] = self.request.GET.get('user', None)
        return super().get_object()

    def get_data(self):
        data = self.request.GET
        return {
            'title': data.get('title', 'Unknown Flag'),
            'modflag': data.get('mod', False) == 'modonly',
        }

    def flag_added(self, obj, **data):
        self.record_action(instance=obj, added=True, **data)

    def flag_removed(self, obj, **data):
        self.record_action(instance=obj, added=False, **data)

    def get_flag(self):
        """Return the flag emoji"""
        if 'flag' in self.request.GET:
            return self.request.GET['flag']
        raise Http404("Can't find flag to toggle.")

class UserModToggle(UserFlagToggle):
    """Toggle on and off the moderator status of a user"""
    def get_flag(self):
        return UserFlag.FLAG_MODERATOR

    def flag_added(self, obj, **data):
        obj.set_moderator(True)
        return super().flag_added(obj, **data)

    def flag_removed(self, obj, **data):
        obj.set_moderator(False)
        return super().flag_removed(obj, **data)


class UserBanToggle(UserFlagToggle):
    """Toggle the banning of users"""
    def get_flag(self):
        return UserFlag.FLAG_BANNED
