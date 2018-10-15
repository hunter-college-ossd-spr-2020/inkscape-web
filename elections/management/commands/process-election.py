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
"""Move the election forwards automatically"""

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from elections.models import Election

class Command(BaseCommand):
    help = "Advance Election"

    @staticmethod
    def handle(**options):
        """Handle the call to the election handle"""
        today = now().date()
        for election in Election.objects.exclude(status='F'):
            if election.status == '.' and election.invite_from <= today:
                election.invitation_open()
            elif election.status == 'N' and election.accept_from <= today:
                election.invitation_close()
            elif election.status == 'S' and election.voting_from <= today:
                election.voting_open()
            elif election.status == 'V' and election.finish_on <= today:
                election.voting_close()
