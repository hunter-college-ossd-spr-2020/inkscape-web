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
Specific haystack controls.
"""

import os

from django.db.models.signals import post_save, post_delete
from django.apps import apps
from django.conf import settings

from haystack.signals import BaseSignalProcessor
from haystack.utils import get_identifier

try:
    from xapian import DatabaseLockError
except ImportError:
    DatabaseLockError = ValueError

class LimitedSignalProcessor(BaseSignalProcessor):
    """
    Half way between the RealtimeSignalProcessor and none, this
    allows you to configure which models should have real time
    haystack full text indexing.

    It also captures xapian locking errors and saves a queue
    for later processing.
    """
    models = getattr(settings, 'HAYSTACK_REALTIME_MODELS', [])
    queue_dir = os.path.join(settings.PROJECT_PATH, 'data', '.xapian.queue')

    @classmethod
    def handle_lock(cls, method, instance):
        """Queue the instance update for later writing"""
        path = os.path.join(cls.queue_dir, method)
        if not os.path.isdir(path):
            os.makedirs(path)

        target = os.path.join(path, get_identifier(instance))

        with open(target, 'a') as fhl:
            fhl.write('1')

    def handle_save(self, sender, instance, **kwargs):
        try:
            super().handle_save(sender, instance, **kwargs)
        except DatabaseLockError:
            self.handle_lock('update', instance)

    def handle_delete(self, sender, instance, **kwargs):
        try:
            super().handle_delete(sender, instance, **kwargs)
        except DatabaseLockError:
            self.handle_lock('remove', instance)

    def get_models(self):
        """Yield model classes"""
        for name in self.models:
            (app_name, model_name) = name.split('.', 1)
            yield apps.get_model(app_label=app_name, model_name=model_name)

    def setup(self):
        """Setup listeners for each of the realtime models"""
        for model in self.get_models():
            post_save.connect(self.handle_save, sender=model)
            post_delete.connect(self.handle_delete, sender=model)

    def teardown(self):
        """Teardown listeners for each of the realtime models"""
        for model in self.get_models():
            post_save.disconnect(self.handle_save, sender=model)
            post_delete.disconnect(self.handle_delete, sender=model)
