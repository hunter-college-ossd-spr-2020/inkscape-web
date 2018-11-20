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

from django_comments.models import CommentFlag
from django_comments.admin import CommentsAdmin

from django.contrib.admin import ModelAdmin, site, TabularInline

from .models import ForumGroup, Forum, ForumTopic, CommentAttachment, UserFlag

class UserFlagAdmin(ModelAdmin):
    raw_id_fields = ('user',)
    list_filter = ('flag',)

site.register(UserFlag, UserFlagAdmin)
site.register(ForumGroup)
site.register(Forum)
site.register(ForumTopic)

class FlagInline(TabularInline):
    raw_id_fields = ('user',)
    model = CommentFlag
    extra = 0

class AttachmentsInline(TabularInline):
    raw_id_fields = ('resource',)
    model = CommentAttachment
    extra = 0

CommentsAdmin.inlines = (FlagInline, AttachmentsInline)
