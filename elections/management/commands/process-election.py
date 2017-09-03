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

from elections.models import Election

class Command(NoArgsCommand):
    help = "Advance Election"

    def handle_noargs(self, **options):
        today = now().date()
        for election in Election.objects.exclude(status='F'):
            if election.status == 'P' and election.invite_from < today:
                election.invitation_open()
            elif election.status == 'I' and election.accept_from < today:
                election.invitation_close()
            elif election.status == 'A' and election.voting_from < today:
                election.voting_open()
            elif election.status == 'V' and election.finish_on < today:
                election.voting_close()

