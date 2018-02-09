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
Notification of new news being published.
"""

from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from alerts.base import BaseAlert, django_signals
from alerts.fields import MultipleCheckboxField

from .models import News


class NewNewsAlert(BaseAlert):
    sender   = News

    name     = _("News Published")
    desc     = _("When the site has new published news, you will get a notification.")
    info     = _("When the website publishes news articles, this notification can send you emails about it. An RSS feed is available as an alternative.")

    subject       = "{% trans 'Inkscape News:' %} {{ instance.title }}"
    email_subject = "{% trans 'Inkscape News:' %} {{ instance.title }}"
    object_name   = "{{ object.title }}"

    subscribe_all = True
    subscribe_any = False
    subscribe_own = False

    filter_field = MultipleCheckboxField(label=_('News Language'),
        required=False, choices=settings.LANGUAGES,
        help_text=_('Limit the news to this language only. Default is all '
            'news languages.'))

    def call(self, sender, instance, **kwargs):
        if instance.is_published:
            return super(NewNewsAlert, self).call(sender, instance=instance, **kwargs)
        return False

    def show_settings_now(self, user):
        return user.alert_subscriptions.filter(alert__slug=self.slug).count() > 0

    def filter_subscriber(self, user, setting, kw):
        """Same as CMSDIFF alert"""
        lang = '|%s|' % (kw['instance'].language or 'en')
        return setting is None or setting.filter_value in ['', None] or lang in setting.filter_value

