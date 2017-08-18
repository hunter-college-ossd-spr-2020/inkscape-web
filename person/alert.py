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
Team and User Alerts
"""

from django.utils.translation import ugettext_lazy as _

from django.utils.translation import get_language
from django.db.models.signals import m2m_changed

from alerts.base import BaseAlert
from .models import Team, TeamMembership


class RequestToJoinAlert(BaseAlert):
    name     = _("Request to Join Team")
    desc     = _("A user has asked to join a team.")
    info     = _("When a user requests to join a team, but the team requires approval, a notification is sent to admins.")

    signal        = None
    sender        = TeamMembership
    subject       = "{% trans 'Team request:' %} {{ instance.team }}"
    email_subject = "{% trans 'Team request:' %} {{ instance.team }}"
    object_name   = "Team '{{ object.team }}' join request"

    subscribe_all = False
    subscribe_any = False
    subscribe_own = True

    def show_settings_now(self, user):
        """
        Show settings if the user is an admin for any team or is a peer in a
        peer enrolement team.
        """
        if user.admin_teams.count() > 0:
            return True
        for membership in user.memberships.objects.filter(team__enrole='P'):
            if membership.joined and not membership.expired:
                return True
        return False

    def get_alert_users(self, instance):
        """Returns either admin or a list of peers depending on enrollment"""
        return instance.team.peers

