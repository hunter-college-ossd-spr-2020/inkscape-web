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
Election Alerts, this section is fairly important as elections MUST keep
everyone up to date about what stage the election is at and what they
must do next.
"""
from django.utils.translation import override as tr_override, ugettext_lazy as _
from django.core.mail.message import EmailMultiAlternatives
from django.conf import settings

from alerts.base import EditedAlert, CreatedAlert
from alerts.template_tools import render_template, render_directly

from .models import Candidate

class CandidateInvitationAlert(CreatedAlert):
    name   = _("Invitation to Stand")
    desc   = _("An alert is sent when a user invites another to stand in an election.")
    info   = _("When a member of a team selects another user to stand, you get an email.")
    sender = Candidate

    email_subject = "{% trans 'Stand for Election:' %} {{ instance.election }}"
    email_footer  = None
    default_email = True

    subscribe_all = False
    subscribe_any = False
    subscribe_own = True

    show_settings = False

    def get_alert_users(self, instance):
        """Alert the candidate that is invited"""
	if instance.user_id != instance.invitor_id:
	    return instance.user


def send_team_email(team, subject, template, **context):
    """Sends a team email to everyone"""
    email = team.email
    if not email:
        email = team.admin.email
        # Do not translate this text to the administrator
        subject = "ADMIN WARNING! No group email set for team '%s'" % team.name
    return send_email(email, subject, template, **context)

DEFAULT_LANG = getattr(settings, 'LANGUAGE_CODE', 'en')

def send_email(email, subject, template, lang=DEFAULT_LANG, **context):
    with tr_override(lang):
        context['site'] = settings.SITE_ROOT
        return EmailMultiAlternatives(
          to=[email],
          body=render_template(template, context),
          subject=render_directly(subject, context)\
            .strip().replace('\n', ' ').replace('\r', ' '),
        ).send(True)


