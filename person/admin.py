#
# Copyright 2013, Martin Owens <doctormo@gmail.com>
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

from django.utils.translation import ugettext_lazy as _

from django.forms import *
from django.contrib.admin import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Permission

from ajax_select import make_ajax_field, make_ajax_form
from ajax_select.admin import AjaxSelectAdmin, AjaxSelectAdminTabularInline

# Add permission to admin so we can remove old stuff
class PermissionAdmin(ModelAdmin):
    list_display = ('name', 'content_type', 'codename')
    search_fields = ('name', 'codename')
    list_filter = ('content_type',)

site.register(Permission, PermissionAdmin)

from .models import *
from .forms import TeamForm

class ChatRoomInline(AjaxSelectAdminTabularInline):
    model = TeamChatRoom
    form = make_ajax_form(TeamChatRoom, {'admin': 'user'}, show_help_text=True)
    fields = ('channel', 'language', 'admin')

class TeamAdmin(AjaxSelectAdmin):
    form = make_ajax_form(Team, {'admin': 'user'}, TeamForm, show_help_text=True)
    list_display = ('name', 'group', 'admin', 'enrole')
    inlines = (ChatRoomInline,)

site.register(Team, TeamAdmin)


class UserAdmin(BaseUserAdmin):
    search_fields = ('username', 'first_name', 'last_name', 'bio', 'ircnick', 'email')
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_admin')
    list_filter = ('is_admin', 'is_superuser', 'is_active', 'groups')
    readonly_fields = ('photo_preview',)
    # We make a copy of the fieldsets from the UserAdmin class so we can
    # customise it without any compelxity. Copied from Django 1.8.
    fieldsets = ( 
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'language',
                              'bio', 'gpg_key', 'photo_preview', 'photo')}),
        (_('Groups and Permissions'),
            {'fields': ('is_active', 'is_admin', 'is_superuser', 'groups',
                'user_permissions'), 'classes': ('collapse', 'close'),}),
        (_('Social Networks'),
            {'fields': ('website', 'ircnick', 'dauser', 'ocuser', 'tbruser'),
                'classes': ('collapse', 'close')}),
        (_('Important dates'),
            {'fields': ('last_login', 'date_joined', 'last_seen', 'visits'),
                'classes': ('collapse', 'close')}),
    ) 

site.register(User, UserAdmin)

class MembershipAdmin(AjaxSelectAdmin):
    form = make_ajax_form(TeamMembership, {
        'user': 'user',
        'added_by': 'user',
        'removed_by': 'user',
    }, show_help_text=True)
    list_filter = ('joined', 'requested', 'expired', 'team')
    list_display = ('repr', 'requested', 'joined', 'expired', 'title')

    def repr(self, obj):
        return "%s membership of %s" % (str(obj.user), str(obj.team))


site.register(TeamMembership, MembershipAdmin)

