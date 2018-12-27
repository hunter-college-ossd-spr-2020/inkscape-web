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
Update all forum counts (in case they get out of sync and init)
"""

import logging

from django.db.models import Q
from django.core.management.base import BaseCommand
from forums.models import UserFlag
from person.models import User

class Command(BaseCommand):
    help = "Run very rarely to make sure moderators are flagged correctly."

    def handle(self, **_):
        """Makes sure moderators have the right flags"""
        flags = UserFlag.objects.all()
        mods = flags.moderators().values_list('user_id', flat=True)
        for user in User.objects.filter(pk__in=mods):
            if not user.is_moderator():
                print("User {} is not moderator (UNFLAG!)".format(user))
                flags.filter(user=user, flag=UserFlag.FLAG_MODERATOR).delete()
        for x, user in enumerate(User.objects.filter(\
            Q(groups__isnull=False) | Q(user_permissions__isnull=False)).distinct()):
            if x % 100 == 0:
                print("Processed {} users".format(x))
            if user.is_moderator() and user.pk not in mods:
                print("User {} is moderator (FLAGGED!)".format(user))
                UserFlag.objects.get_or_create(user=user, flag=UserFlag.FLAG_MODERATOR,
                                               defaults={'title': "Moderator"})
