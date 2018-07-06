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
"""Takes 20 random people from randomuser.me and installs them into the site."""

import json
import urllib

from django.core.management.base import BaseCommand
from django.core.files.temp import NamedTemporaryFile
from django.core.files.base import File

from person.models import Group, User

class Command(BaseCommand):
    """Provide a command for creating users"""
    help = __doc__

    def url_file(self, url):
        """Download the given url file"""
        img_temp = NamedTemporaryFile()
        opener = urllib.request.build_opener()
        img_temp.write(opener.open(url).read())
        img_temp.flush()
        return File(img_temp)

    def handle(self, number=20, **options):
        """Handle creating this number of users"""
        url = 'https://randomuser.me/api/?results={:d}'.format(number)
        response = urllib.request.urlopen(url)
        groups = Group.objects.filter(team__isnull=False).order_by('?')
        for datum in json.load(response)['results']:
            (user, _) = User.objects.get_or_create(
                username=datum['login']['username'],
                defaults={
                    'first_name': datum['name']['first'],
                    'last_name': datum['name']['last'],
                    'email': datum['email'],
                })
            user.photo.save(datum['login']['username']+'.jpg',\
                self.url_file(datum['picture']['large']))
            user.save()
            for group in groups[:2]:
                group.user_set.add(user)
            print("Added {} added to {}".format(user, user.groups.all()))


