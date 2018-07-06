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

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.utils.timezone import now

from person.models import *

class Command(NoArgsCommand):
    help = "Sync group memberships so that teams are aware of groups"

    def handle_noargs(self, **options):
        for team in Team.objects.all():
            print(" * %s" % unicode(team))
            users = set()
            for user in team.group.user_set.all():
                users.add(user.pk)
                if not team.has_member(user):
                    print("  + %s" % unicode(user))
                    team.update_membership(user, expired=None, joined=now()) 

            for membership in team.members:
                if membership.user.pk not in users:
                    print("  - %s" % unicode(membership.user))
                    team.update_membership(membership.user, expired=now())

