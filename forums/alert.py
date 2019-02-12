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
from django import forms

from alerts.base import BaseAlert
from alerts.models import AlertSubscription, UserAlert

from .models import Forum, ForumTopic

class ForumAlert(BaseAlert):
    """
    Allow users to subscribe to a whole forum (lots of messages!)
    """
    name = _("Form Updated")
    desc = _("Activity on an entire forum you are subscribed to")
    info = _("When a user creates a new topic or posts to an existing one in a forum you've subscribed to.")
    sender = Forum

    # No automatic signal, used by ForumTopicAlert with no signal itself.
    signal = None

    subscribe_all = False
    subscribe_any = True
    subscribe_own = False

class ForumTopicAlert(BaseAlert):
    """
    Allow users to subscribe to forum topics and email them when things change.
    """
    name = _("Forum Topic Updated")
    desc = _("Activity on a forum topic you are subscribed to")
    info = _("When a user adds or edits a forum post in a topic you have subscribed to.")
    sender = ForumTopic

    # No automatic signal, called from app.py when needed
    signal = None

    subject = "{% trans 'Forum topic activity on:' %} {{ instance }}"
    object_name = "{% trans 'Topic activty' %}"
    email_subject = "{% trans 'Forum activity on:' %} {% autoescape off %}{{ instance }}{% endautoescape %}"
    default_email = True

    subscribe_all = False
    subscribe_any = True
    subscribe_own = False

    def get_custom_fields(self, data, user=None):
        """Get some subscription settings"""
        return [('auto', forms.BooleanField(required=False,\
                 initial=True, label=_("Automatic"),\
                 help_text=_("Automatically subscribe to any topic I reply to.")))]

    def post_send(self, *alerts, **kwargs):
        """Over-ride to add forum subscribers and remove own user from list."""
        alerts = list(alerts)
        forum = getattr(kwargs['instance'], 'forum', None)
        if forum is None:
            return super().post_send(*alerts, **kwargs)
        users = [alert.user for alert in alerts]
        for sub in ForumAlert.get_alert_type().subscriptions.filter(target=forum.pk):
            if sub.user in users:
                continue
            if self._filter_subscriber(sub.user, kwargs, 'any'):
                ret = self.alert_type.send_to(sub.user, **kwargs)
                if ret and isinstance(ret, list):
                    alerts += ret
        return super().post_send(*alerts, **kwargs)

    @classmethod
    def auto_subscribe(cls, user, topic):
        """Add the user to the topic"""
        alert = cls.get_alert_type()
        settings = user.alert_settings.get(alert=alert).get_custom_settings()
        if settings.get('auto', True):
            return alert.subscriptions.get_or_create(user=user, target=topic.pk)[1]
        return False

    @classmethod
    def subscriptions_for(cls, user):
        """Return a list of subscriptions for this user"""
        if user is not None and user.is_authenticated():
            return user.alert_subscriptions.filter(alert__slug=cls.slug)
        return AlertSubscription.objects.none()

    @classmethod
    def messages_for(cls, user, new=True):
        """Returns a list of messages for the user"""
        alert = cls.get_alert_type()
        qset = UserAlert.objects.filter(alert_id=alert.pk, user_id=user.pk)
        qset = qset.filter(deleted__isnull=True)
        if new:
            qset = qset.filter(viewed__isnull=True)
        return qset

    def get_filter_subscriber(self, user, setting, kwargs, sub_type):
        """
        Filters subscriber messages, removing messages to myself
        """
        comment = kwargs.get('comment', None)
        if comment is not None:
            return comment.user_id != user.pk
        return False
