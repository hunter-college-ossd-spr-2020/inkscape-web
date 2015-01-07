#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Inherit from these classes if you want to create your own alert connections.
"""
__all__ = ['register_type', 'register_alert', 'BaseAlert', 'EditedAlert', 'CreatedAlert', 'SIGNALS']

from django.db.models import signals as django_signals
from .base import *

import sys

ALERT_TYPE = None
def register_type(cls):
    global ALERT_TYPE
    ALERT_TYPE = cls

SIGNALS = {}
def register_alert(slug, cls, **kwargs):
    global ALERT_TYPE
    if not ALERT_TYPE:
        raise AttributeError("No alert type set!")
    kwargs.update({
      'enabled': True,
      'category': cls.category,
      'default_hide' : cls.default_hide,
      'default_email' : cls.default_email,
    })
    # XXX Created datetime could be checked against the file of the cls
    # so items canbe updated with changes (especially for default options)
    (item, created) = ALERT_TYPE.objects.get_or_create(slug=slug, defaults=kwargs)
    SIGNALS[slug] = (item, cls(slug))
    cls.signal.connect(SIGNALS[slug][1].call, sender=cls.sender, dispatch_uid=slug)
    #responses = cls.signal.send(cls.sender, instance=cls.sender.objects.all()[0], created=True)
    #sys.stderr.write("Responses: %s\n" % str(responses))


class BaseAlert(object):
    """None model parent class for your alert signals"""
    # We really don't want to allow anyone to subscribe to
    # all private messages, so we add a flag to ensure them.
    private       = False
    # These defaults control how messages should be displayed or
    # Send via email to the user's email address.
    default_hide  = False
    default_email = True

    signal   = django_signals.post_save
    category = CATEGORY_UNKNOWN
    sender   = None

    subject  = "{{ object }}"
    email_subject = "Website Alert: {{ object }}"

    def __init__(self, slug):
        self.slug = slug

    def get_type(self):
        return SIGNALS[self.slug][0]

    def call(self, sender, **kwargs):
        """Connect this method to the post_save signal and it will
           create an alert when the sender edits any object."""
        if self.get_type().enabled:
            return self.get_type().send_from(self, sender, **kwargs)

    def format_data(self, data):
        """Overridable function to format data for the template"""
        return data

    @property
    def template(self):
        n = "alerts/type/%s.html" % self.slug
        if has_template(n):
            return n
        return "alerts/type_default.html"

    @property
    def email_template(self):
        n = "alerts/email_%s.txt" % self.slug
        if has_template(n):
            return n
        return "alerts/email_default.txt"

    @property
    def name(self):
        raise NotImplementedError("Name is a required property for alerts.")

    @property
    def desc(self):
        raise NotImplementedError("Desc is a required property for alerts.")


class EditedAlert(BaseAlert):
    def call(self, sender, instance, **kwargs):
        if not kwargs.get('created', False):
            return super(CreatedAlert, self).call(sender, instance=instance, **kwargs)
        return False

class CreatedAlert(BaseAlert):
    def call(self, sender, instance, **kwargs):
        if kwargs.get('created', False):
            return super(CreatedAlert, self).call(sender, instance=instance, **kwargs)
        return False

