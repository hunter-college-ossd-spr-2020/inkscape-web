#
# Copyright 2013, Martin Owens <doctormo@gmail.com>
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
Returns the id for a single user. This is used to migrate backups for use locally.
"""
from django.core.management import BaseCommand
from person.models import User

class Command(BaseCommand):
    """Command for returning a user id"""
    help = __doc__

    def handle(self, *args, **options):
        if User.objects.count() == 0:
            raise ValueError("No valid user is available for use.")
        for x, user in enumerate(User.objects.all().order_by('?')):
            # TODO: In the future we can check validity here.
            print(user.id)
            if x > 30:
                return
