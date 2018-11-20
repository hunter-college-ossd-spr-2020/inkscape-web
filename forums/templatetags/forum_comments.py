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
from django_comments.templatetags.comments import CommentListNode

register = Library() # pylint: disable=invalid-name

class ForumCommentListNode(CommentListNode):
    """Tweaks for forum comment listing"""
    def get_queryset(self, context):
        qset = super().get_queryset(context)
        qset = qset.prefetch_related('flags', 'attachments', 'attachments__resource',
                                     'user', 'user__forum_flags')\
                   .defer('user_email', 'user_name', 'user_url', 'ip_address',
                          'user__password', 'user__email', 'user__bio', 'user__ircnick',
                          'user__ircpass', 'user__dauser', 'user__ocuser', 'user__tbruser',
                          'user__gpg_key', 'user__last_seen', 'user__visits', 'user__website')
        return qset

@register.tag
def get_forum_comment_list(parser, token):
    """
    See django_comments.templatetags.comments.get_comment_list
    """
    return ForumCommentListNode.handle_token(parser, token)
