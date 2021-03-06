#
# Copyright (C) 2016, Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Try to make forum comment requests faster.
"""

from django.template import Library
from django_comments.templatetags.comments import CommentListNode, CommentFormNode

from alerts.models import AlertSubscription

from ..forms import AddCommentForm

register = Library() # pylint: disable=invalid-name

def defer(base, *args):
    """Build a quick deferment list"""
    for arg in args:
        if isinstance(arg, str):
            yield base + '__' + arg
        else:
            for subarg in arg:
                yield base + '__' + subarg

FORUM_DEFER = ['user_email', 'user_name', 'user_url', 'ip_address'] + \
    list(defer('user', 'password', 'email', 'bio', 'ircnick', 'ircpass', 'dauser', 'ocuser',
               'tbruser', 'gpg_key', 'last_seen', 'visits', 'website'))
FORUM_PREFETCH = ['flags', 'attachments', 'attachments__resource', 'user', 'user__forum_flags']

#
# === Comment List === #
#

class ForumCommentListNode(CommentListNode):
    """Tweaks for forum comment listing"""
    def get_queryset(self, context):
        ctype, object_pk = self.get_target_ctype_pk(context)
        if not object_pk:
            return self.comment_model.objects.none()

        # We show all is_public=False so moderators can see them
        qset = self.comment_model.objects.filter(object_pk=object_pk, content_type=ctype)
        qset = qset.filter(is_removed=False)
        return qset.prefetch_related(*FORUM_PREFETCH).defer(*FORUM_DEFER)

@register.tag
def get_forum_comment_list(parser, token):
    """
    See django_comments.templatetags.comments.get_comment_list
    """
    return ForumCommentListNode.handle_token(parser, token)

@register.filter("subscription")
def sub(topic, user):
    """Return if the user is subscribed to the topic"""
    try:
        return topic.subscriptions.get(user_id=user.pk)
    except AlertSubscription.DoesNotExist:
        return None

#
# === Comment Form === #
#

class ForumCommentFormNode(CommentFormNode):
    """
    Load the forum form instead with the right vars
    """
    def get_form(self, context):
        obj = self.get_object(context)
        if obj:
            request = context['request']
            return AddCommentForm(
                user=request.user,
                ip_address=request.META.get("REMOTE_ADDR", None),
                target_object=obj,
            )
        return None

@register.tag
def get_forum_comment_form(parser, token):
    """
    See django_comments.templatetags.comments.get_comment_form
    """
    return ForumCommentFormNode.handle_token(parser, token)
