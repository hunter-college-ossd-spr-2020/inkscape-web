#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
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
# pylint: disable=no-member,too-few-public-methods
"""
Basic mixin classes for forums
"""
import json

from django.db.models import Q
from django.utils import translation

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator, decorator_from_middleware
from django.views.decorators.csrf import csrf_exempt

from .middleware import RecentUsersMiddleware
from .models import Forum, ForumTopic, Comment

class UserVisit(object):
    """Record that a user visited this page"""
    @decorator_from_middleware(RecentUsersMiddleware)
    def dispatch(self, request, *args, **kwargs):
        """Empty dispatch for running middleware decorator"""
        return super().dispatch(request, *args, **kwargs)

class UserRequired(object):
    """Only allow a logged in user for flagging"""
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """Add login_required decorator to dispatch"""
        if hasattr(self, 'is_allowed') and not self.is_allowed(request.user):
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

class ModeratorLogged(object):
    """Log each action that a moderator does"""
    def log_details(self):
        """Return important information about the changes"""
        return {}

    def record_action(self):
        """Record the action taken here as a moderation action"""
        owner = getattr(self, 'owner', False)
        if not hasattr(self, 'moderation_action') and not owner:
            obj = self.get_object()
            if isinstance(obj, Comment):
                self.record_comment_action(obj)
            elif isinstance(obj, ForumTopic):
                self.record_topic_action(obj)

    def record_comment_action(self, comment):
        """Record the action taken against a comment"""
        self.moderation_action = \
            self.request.user.forum_moderation_actions.create(
                action=type(self).__name__,
                user=comment.user,
                topic=comment.get_topic(),
                comment=comment,
                detail=json.dumps(self.log_details()))

    def record_topic_action(self, topic):
        """Record the action taken against a forum topic"""
        comment = topic.comments.first()
        self.moderation_action = \
            self.request.user.forum_moderation_actions.create(
                action=type(self).__name__,
                user=comment.user,
                topic=topic,
                comment=comment,
                detail=json.dumps(self.log_details()))

    def form_valid(self, form):
        """Record when the form is valid"""
        ret = super().form_valid(form)
        self.record_action()
        return ret

    def get_success_url(self):
        """Record when getting a success url"""
        ret = super().get_success_url()
        self.record_action()
        return ret

class ModeratorRequired(ModeratorLogged, UserRequired):
    """Restrict to just moderators permission"""
    @staticmethod
    def is_allowed(user):
        """Only moderators can see this"""
        return user.is_moderator()

class OwnerRequired(ModeratorLogged, UserRequired):
    """Restrict to the owner of an object or the moderator"""
    def is_allowed(self, user):
        """Make sure only owners can do or see this view, or is a moderator"""
        obj = self.get_object()
        self.owner = obj.user == user
        return self.owner or user.is_moderator()

class ForumMixin(object):
    """Provide standard outputs for forum listings"""
    def get_forum_list(self):
        """Return a standard list of forums"""
        qset = Forum.objects.all()
        if not self.request.GET.get('all'):
            language = translation.get_language()
            qset = qset.filter(Q(lang=language) | Q(lang='') | Q(lang__isnull=True))
        return qset.select_related('group')

    def get_context_data(self, **kwargs):
        """Add standard context data elements"""
        data = super().get_context_data(**kwargs)
        data['forums'] = self.get_forum_list()
        return data

class CsrfExempt(object):
    """Exempt a form from cross-scripting protections"""
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """Wrap the csrf_exempt decorator"""
        return super().dispatch(request, *args, **kwargs)
