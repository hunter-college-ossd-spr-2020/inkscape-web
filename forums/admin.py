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
Admin interfaces for comments and forums.
"""

from django_comments.models import CommentFlag, Comment
from django_comments.admin import CommentsAdmin

from django.utils.text import mark_safe
from django.contrib.admin import ModelAdmin, register, TabularInline
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import (
    ForumGroup, Forum, ForumTopic, CommentAttachment,
    UserFlag, ModerationLog, BannedWords
)

@register(ModerationLog)
class ModerationLogAdmin(ModelAdmin):
    list_display = ('action', 'moderator', 'performed', 'comment')
    list_filter = ('action',)
    raw_id_fields = ('moderator', 'user', 'comment', 'topic', 'forum')

@register(UserFlag)
class UserFlagAdmin(ModelAdmin):
    raw_id_fields = ('user',)
    list_filter = ('flag',)


@register(ForumGroup)
class ForumGroupAdmin(ModelAdmin):
    list_display = ('name', 'sort', 'forum_list')

    def forum_list(self, obj):
        return mark_safe('' + ' '.join([
            "<a class='errornote' href='{}'>{}</a>".format(item.get_absolute_url(), item.name) for item in obj.forums.all()
        ]) + '')

@register(Forum)
class ForumAdmin(ModelAdmin):
    list_filter = ('group', 'team')
    search_fields = ('name', 'desc')
    list_display = ('name', 'desc', 'group', 'team', 'lang', 'post_count', 'last_posted')
    readonly_fields = ('post_count', 'last_posted')


class CommentInline(GenericTabularInline):
    model = Comment
    ct_fk_field = 'object_pk'
    ct_field = 'content_type'
    raw_id_fields = ('user',)
    readonly_fields = ('site', 'ip_address', 'submit_date', 'user_url')

@register(BannedWords)
class WordsAdmin(ModelAdmin):
    search_fields = ('phrase',)
    list_display = ('phrase', 'in_title', 'in_body', 'new_user', 'ban_user', 'found_count', 'moderator', 'created')
    readonly_fields = ('found_count',)
    raw_id_fields = ('moderator',)

@register(ForumTopic)
class TopicAdmin(ModelAdmin):
    inlines = [CommentInline]
    list_filter = ('forum',)
    search_fields = ('subject',)
    list_display = ('subject', 'forum', 'last_posted', 'last_username',
                    'locked', 'removed', 'sticky', 'post_count')
    readonly_fields = (
        'post_count', 'last_posted', 'last_posted',
        'first_username', 'last_username', 'has_attachments',
    )


class FlagInline(TabularInline):
    raw_id_fields = ('user',)
    model = CommentFlag
    extra = 0

class AttachmentsInline(TabularInline):
    raw_id_fields = ('resource',)
    model = CommentAttachment
    extra = 0

CommentsAdmin.inlines = (FlagInline, AttachmentsInline)
