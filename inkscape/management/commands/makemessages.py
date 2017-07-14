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
Django command for clearing fastly caches.
"""
import os

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.commands.makemessages import Command as BaseCommand

class Command(BaseCommand):
    help = "Make messages, including apps as configured."

    def handle(self, *args, **options):
        if options.pop('all', True):
            options['locale'] = zip(*settings.LANGUAGES)[0]
        self.apps = options.pop('apps', None)

        super(Command, self).handle(*args, **options)

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--app', '-m', default=[], dest='apps', action='append',
            help='Only scan the contents of these apps, default will scan all folders.')

    def find_files(self, root):
        if self.apps:
            ab_root = os.path.abspath(root)
            files = []
            for app_name in self.apps:
                app = apps.get_app_config(app_name)
                path = app.path.replace(ab_root, root)
                files += super(Command, self).find_files(path)
            return files
        return super(Command, self).find_files(root)

