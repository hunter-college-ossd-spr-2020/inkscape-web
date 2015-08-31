#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
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
Inherit from these classes if you want to create your own alert connections.
"""
__all__ = ['BaseAlert', 'EditedAlert', 'CreatedAlert']

from django.db.models import Q
from django.db.models import signals as django_signals
from django.contrib.auth.models import User, Group
from django.core.mail.message import EmailMultiAlternatives

from alerts.tools import has_template, render_template, render_directly
from alerts.models import UserAlert, UserAlertManager, AlertType

import os
import sys
import re

ALL_ALERTS = {}

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
    category = AlertType.CATEGORY_UNKNOWN
    sender   = None

    # What lookup should be attached to the sender model;
    # much like ForeignKey related_name it creates reverse lookups.
    related_name = 'alerts'

    subject  = "{{ instance }}"
    email_subject = "{% trans 'Website Alert:' %} {{ instance }}"
    email_footer = 'alerts/alert/email_footer.txt'
    object_name = "{{ instance }}"

    # User specifies which user attribute on the instance alerts are sent
    alert_user  = '.'
    alert_group = '.'

    # Should we load only on test suite run.
    test_only = False

    # Target is the attribute on the instance which subscriptions are bound
    target_field = None

    def __init__(self, slug, **kwargs):
        self.slug = slug

        # Check the setup of this alert class
        if not self.sender:
            raise AttributeError("%s required 'sender' attribute" %
                type(self).__name__)
        if hasattr(self.sender, self.related_name):
            raise AttributeError("%s already has '%s' reverse lookup" % (
                self.sender.__name__, self.related_name))

        super(BaseAlert, self).__init__(**kwargs)

        # Global registration so this is a singleton.
        if slug in ALL_ALERTS:
            raise KeyError("Alert can not be registered twice: %s" % slug)
        ALL_ALERTS[slug] = self

        try:
            # Create an AlertType object which mirrors this class
            (self.alert_type, created) = AlertType.objects.get_or_create(
              slug=slug,
              values={
                'enabled': True,
                'private': self.private,
                'category': self.category,
                'default_hide' : self.default_hide,
                'default_email' : self.default_email,
              })
        except Exception as error:
            raise type(error)("Couldn't setup Alert: %s" % str(error))
        else:
            self.signal.connect(self.call, sender=self.sender, dispatch_uid=self.slug)

        class ManagerDescriptor(object):
            """This descriptor is a class and object property as needed"""
            def __get__(desc, obj, klass=None):
                manager = UserAlertManager(obj, self.alert_type)
                manager.model = UserAlert
                return manager

        # Set reverse lookup, the related name defaults to 'alerts'
        setattr(self.sender, self.related_name, ManagerDescriptor())

    def call(self, sender, **kwargs):
        """Connect this method to the post_save signal and it will
           create an alert when the sender edits any object."""
        def send_to(recipient, kind=None):
             if kind is None or isinstance(recipient, kind):
                 return self.alert_type.send_to(recipient, **kwargs)

        instance = kwargs['instance']
        send_to(getattr(instance, self.alert_user, None), User)
        send_to(getattr(instance, self.alert_group, None), Group)

        if not self.private:
            target = instance
            if self.target_field:
                target = getattr(instance, self.target_field)

            q = Q(target__isnull=True) | Q(target=target.pk)
            for sub in self.alert_type.subscriptions.filter(q):
                send_to(sub.user)
        # TODO: send_to returns a list of users sent to, but we don't log much here.

    @property
    def instance_type(self):
        if self.target_field:
            return self.sender._meta.get_field(self.target_field).rel.to
        return self.sender

    @property
    def template(self):
        n = "%s/alert/%s.html" % tuple(self.slug.split('.', 1))
        if has_template(n):
            return n
        return "alerts/type_default.html"

    @property
    def email_template(self):
        n = "%s/alert/email_%s.txt" % tuple(self.slug.split('.', 1))
        if has_template(n):
            return n
        return "alerts/email_default.txt"

    @property
    def name(self):
        raise NotImplementedError("Name is a required property for alerts.")

    @property
    def desc(self):
        raise NotImplementedError("Desc is a required property for alerts.")

    def get_object(self, **fields):
        """Returns object matching field using Alert's target object type"""
        model = self.sender
        if self.target_field:
            # Get FoeignKey's mdel linking this alert instead
            model = getattr(model, self.target_field).field.rel.to
        return model.objects.get(**fields)

    def get_object_name(self, obj):
        """Return's a label for this kind of subscription for an object"""
        if obj:
            return render_directly(self.object_name, {'object': obj})
        return None

    def format_data(self, data):
        """Overridable function to format data for the template"""
        return data

    def get_subject(self, context_data):
        return render_directly(self.subject, self.format_data(context_data))

    def get_body(self, context_data):
        return render_template(self.template, context_data)

    def send_email(self, recipient, context_data):
        if not recipient:
            return False

        context_data = self.format_data(context_data)

        subject = render_directly(self.email_subject, context_data)
        subject = subject.strip().replace('\n', ' ').replace('\r', ' ')
        body    = render_template(self.email_template, context_data)
        if self.email_footer is not None:
            body += render_template(self.email_footer, context_data)
        email   = EmailMultiAlternatives(subject, body, None, (recipient,))

        # This will fail silently if not configured right
        return email.send(True)


class EditedAlert(BaseAlert):
    def call(self, sender, instance, **kwargs):
        if not kwargs.get('created', False):
            return super(EditedAlert, self).call(sender, instance=instance, **kwargs)
        return False


class CreatedAlert(BaseAlert):
    def call(self, sender, instance, **kwargs):
        if kwargs.get('created', False):
            return super(CreatedAlert, self).call(sender, instance=instance, **kwargs)
        return False

