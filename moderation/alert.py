#
# Copyright 2017, Martin Owens <doctormo@gmail.com>
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
Moderation alerts
"""
from django.utils.translation import ugettext_lazy as _
from django.dispatch import Signal

from alerts.base import EditedAlert, BaseAlert
from forums.models import Comment

from .models import FlagObject, FlagVote, flag_created

class NewFlagAlert(BaseAlert):
    name     = _("Moderation Alert")
    desc     = _("An alert is sent when any item is flagged for moderation.")
    info     = _("When a user flags a resource, user or comment for moderation, you will get an email.")
    sender   = FlagObject
    signal   = flag_created

    subject       = "{% trans 'Moderator Alert:' %} {{ instance }}"
    email_subject = "{% trans 'Moderator Alert:' %} {{ instance }}"
    object_name   = "{{ object }}"

    default_email = True
    default_irc   = False

    subscribe_all = True
    subscribe_any = False
    subscribe_own = False

    # Only show is user has permissions
    def show_settings_now(self, user):
        return user.has_perm("moderation.can_moderate")


class ModeratorDeletedAlert(EditedAlert):
    name     = _("Moderators Deleted an Item")
    desc     = _("One of your items was deleted by the moderators.")
    info     = _("When a user's item or user's own account is deleted.")
    sender   = FlagObject

    subject       = "{% trans 'Deleted by Moderators:' %} {{ instance.obj }}"
    email_subject = "{% trans 'Deleted by Moderators:' %} {{ instance.obj }}"
    object_name   = "{{ object }}"
    default_email = True

    subscribe_all = False
    subscribe_any = False
    subscribe_own = True
    related_name = 'deleted_alerts'

    # Never show these settings, nailed down
    show_settings = False

    def get_alert_users(self, instance):
        """Return the object_owner only if the resolution was delete"""
        obj = instance.object_owner
        if obj and instance.resolution == False:
            return obj

    def post_send(self, *users, **kw):
        """Delete object after so message can be sent to deleted users."""
        instance = kw['instance']
        if instance.resolution is False and instance.obj:
            instance.obj.delete()
