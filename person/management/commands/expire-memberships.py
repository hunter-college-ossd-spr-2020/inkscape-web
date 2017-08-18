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

from django.core.management.base import NoArgsCommand
from django.utils.timezone import now

from person.models import *

class Command(NoArgsCommand):
    help = "Automatically expire users from team memberships and send out"\
           " reminder notifications/alters when the user is removed."\
           " If the expiration is greater than two weeks, then a warning"\
           " is sent out at the one week mark."

    def handle_noargs(self, **options):
        for team in Team.objects.filter(auto_expire__gt=0):
            for user in team.expire_if_needed(now()):
                print " [EXPIRED] %s " % unicode(user)

            if team.auto_expire > 14:
                for user in team.warn_if_needed(now(), 7):
                    print " [WARNED] %s " % unicode(user)

