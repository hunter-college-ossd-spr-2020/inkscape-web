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
import logging

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.management.commands.makemessages import Command as BaseCommand

CONF_NAME = 'TRANSLATED_APPS'

class Command(BaseCommand):
    help = "Make messages, including apps as configured."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--app', '-m', default=[], action='append',
            dest='apps', help='Only scan the contents of these app folders.')
        parser.add_argument('--configured-list', dest='configured_list',
            action='store_true', help='Load a list of apps from the settings.')

    def handle(self, apps=(), configured_list=False, **options):
        self.apps = list(self.parse_apps(apps, configured_list))
        if self.apps:
            print("Selecting apps: %s" % ", ".join(self.apps))
        super(Command, self).handle(**options)

    @staticmethod
    def parse_apps(in_apps, configured_list):
        for app in list(set(settings.INSTALLED_APPS) & set(in_apps)):
            in_apps.remove(app)
            yield app

        if in_apps:
            raise CommandError("App(s) not found %s" % ", ".join(in_apps))

        if configured_list:
            if hasattr(settings, CONF_NAME):
                for item in getattr(settings, CONF_NAME):
                    yield item
            else:
                raise CommandError("Config %s is not set." % CONF_NAME)

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

