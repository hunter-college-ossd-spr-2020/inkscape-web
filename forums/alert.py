#
# Copyright 2018, Martin Owens <doctormo@gmail.com>
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
Subscriptions and alerts for forums
"""
from django.utils.translation import ugettext_lazy as _

from alerts.base import EditedAlert

from .models import ForumTopic

class ForumTopicAlert(EditedAlert):
    """
    Allow users to subscribe to forum topics and email them when things change.
    """
    name = _("Forum Topic Updated")
    desc = _("Activity on a forum topic you are subscribed to")
    info = _("When a user adds or edits a forum post in a topic you have subscribed to.")
    sender = ForumTopic

    subject = "{% trans 'Forum activity on:' %} {{ instance }}"
    object_name = "{% trans 'Topic activty' %}"
    email_subject = "{% trans 'Forum activity on:' %} {{ instance }}"
    default_email = True

    subscribe_all = False
    subscribe_any = True
    subscribe_own = False