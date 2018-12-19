#
# Copyright 2016-2017, Martin Owens <doctormo@gmail.com>
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
"""Moderation administrative interface"""

from django.contrib.admin import ModelAdmin, TabularInline, site

from .models import FlagObject, FlagVote

class VoteInline(TabularInline):
    """Inline votes in a moderation action"""
    raw_id_fields = ('moderator',)
    model = FlagVote
    extra = 1

class FlagAdmin(ModelAdmin):
    """The original moderation flag object"""
    raw_id_fields = ('object_owner',)
    list_filter = ('resolution',)
    list_display = ('pk', 'obj', 'object_owner', 'flag_votes', 'censure_votes', 'approve_votes')
    inlines = (VoteInline,)

site.register(FlagObject, FlagAdmin)
