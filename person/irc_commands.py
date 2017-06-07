#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
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
Commands related to Users and Teams
"""
import time

from django.db.models import Q
from ircbot.base import BotCommand

from .models import User, Team, TeamChatRoom

class TeamChannels(BotCommand):
    def __init__(self, *args, **kw):
        super(TeamChannels, self).__init__(*args, **kw)
        self.pulse = 0 

    def ready(self):
        """When we're connected we want to update the rooms we're connected to."""
        if self.pulse > 0:
            self.pulse -= 1
            return False

        rooms = self.connection.channels.keys()
        for chatroom in TeamChatRoom.objects.all():
            room = '#' + chatroom.channel
            if room not in rooms:
                self.connection.join(room)
                time.sleep(0.1)
            else:
                rooms.remove(room)

        # Unjoin any rooms not listed
        for room in rooms:
            self.connection.part(room, 'I didn\'t know we \'ad a king!')
            self.connection.channels.pop(room, None)

        # We're never ready, because we want to check again.
        self.pulse = 10 # Wait 10 minutes before re-checking
        return False


class WhoisCommand(BotCommand):
    regex = "whois (\w+)"

    def run_command(self, context, nick):
        users = User.objects.filter(Q(ircnick__iexact=nick) | Q(username__iexact=nick))
        if users.count() > 0:
            return context.nick + ': ' + '\n'.join([u"%s - %s" %
              (str(profile), url(profile)) for profile in users])

        return context.nick + ': ' + _(u'No user with irc nickname "%(nick)s" on the website.') % {'nick': nick}

