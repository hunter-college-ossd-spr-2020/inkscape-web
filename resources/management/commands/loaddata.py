#
# Copyright 2013 Duncan Ingram, Inc. (MIT License)
#
# Copyright 2015, Martin Owens <doctormo@gmail.com>
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
Overloads django's loaddata command so it will install media fixtures
These are collections of files ready to be used with database entries
for example FileField and ImageField.
"""

import os

from django.conf import settings
import django.core.management.commands.loaddata
from django.core.files.base import File
import django.core.serializers
from django.db.models import signals
from django.db.models.fields.files import FileField
from django.utils._os import upath
from django.apps import apps

def models_with_filefields():
    for klass in apps.get_models():
        if any(isinstance(field, FileField) for field in klass._meta.fields):
            yield klass

def find_fixture_paths():
    """Return the full paths to all possible fixture directories."""
    app_module_paths = []
    for app in apps.get_app_configs():

        app_module_paths.append(upath(app.path))

    app_fixtures = [os.path.join(path, 'fixtures') for path in app_module_paths]
    return app_fixtures + list(settings.FIXTURE_DIRS)

GLOBAL_WARN = set()

class Command(django.core.management.commands.loaddata.Command):
    def load_images_for_signal(self, sender, instance, **kwargs):
        not_found = set()
        is_found  = set()

        import sys
        for field in sender._meta.fields:
            if not isinstance(field, FileField):
                continue
            path = getattr(instance, field.attname)
            if path is None or not path.name:
                continue
            for fixture_path in self.fixture_media_paths:
                filepath = os.path.join(fixture_path, path.name)
                try:
                    with open(filepath, 'rb') as fhl:
                        dj_file = File(fhl, path.name)
                        setattr(instance, field.attname, dj_file)
                        n = getattr(instance, field.attname)
                        sys.stderr.write(f"Field: {n.path}\n")
                        is_found.add(path.name)
                        break
                except FileNotFoundError:
                    not_found.add(path.name)

        for filename in (not_found - is_found):
            if filename not in GLOBAL_WARN: # _IsWarning_
                if filename[0] != '/':
                    self.stderr.write(" [skipping] Expected file: %s" % filename)
                GLOBAL_WARN.add(filename)

    def handle(self, *fixture_labels, **options):
        # Hook up pre_save events for all the apps' models that have FileFields.
        for klass in models_with_filefields():
            signals.pre_save.connect(self.load_images_for_signal, sender=klass)

        fixture_paths = find_fixture_paths()
        fixture_paths = (os.path.join(path, 'media') for path in fixture_paths)
        fixture_paths = [path for path in fixture_paths if os.path.isdir(path)]
        self.fixture_media_paths = fixture_paths

        ret = super(Command, self).handle(*fixture_labels, **options)

        # Disconnect all the signals
        for klass in models_with_filefields():
            signals.pre_save.disconnect(self.load_images_for_signal, sender=klass)

        return ret
