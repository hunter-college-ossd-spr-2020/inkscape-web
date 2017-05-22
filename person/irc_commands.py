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

import os
import time
from datetime import datetime, timedelta

from django.db.models import Q
from django.db.models.signals import post_save
from django.conf import settings

from inkscape.management.commands.ircbot import BotCommand

from .models import User, Team, TeamChatRoom

class WhoisCommand(BotCommand):
    regex = "whois (\w+)"

    def run_command(self, context, nick):
        users = User.objects.filter(Q(ircnick__iexact=nick) | Q(username__iexact=nick))
        if users.count() > 0:
            return context.nick + ': ' + '\n'.join([u"%s - %s" %
              (str(profile), url(profile)) for profile in users])

        return context.nick + ': ' + _(u'No user with irc nickname "%(nick)s" on the website.') % {'nick': nick}

class TeamChannels(BotCommand):
    regex = "."

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

    def __call__(self, context, message, *args, **kwargs):
        """Call for any message to this channel"""
        dt = datetime.now()
        if not context.target or not context.target.startswith('#'):
            return False
        if context.msgtype == 'JOIN':
            # Don't log join requests, because we never get PART or
            # QUIT messages, so there's not much point in JOIN requests.
            return
        for chatroom in TeamChatRoom.objects.filter(channel=context.target[1:]):
            dt_time = str(dt.time())
            username = context.ident.nick
            message = message.replace('|', '[pipe]')

            log_file = self.get_log(chatroom, dt)
            if log_file is not None:
                dir_name = os.path.dirname(log_file)
                if not os.path.isdir(dir_name):
                    os.makedirs(dir_name)

                with open(log_file, 'a') as fhl:
                    fhl.write('A|%s|%s|%s\n' % (dt_time, username, message))

    @staticmethod
    def get_log(chatroom, dt):
        path = chatroom.log_path
        if path is not None:
            return os.path.join(path, str(dt.date()) + '.txt')


class RedactLog(BotCommand):
    """Command to remove/redact the logs for a user"""
    regex = "redact ([^\s]+) (\d+)([dhms])"
    units = {'d': 'days', 'h': 'hours', 'm': 'minutes', 's': 'seconds'}

    def run_command(self, context, username, scale, unit):
        if context.target is None:
            return

        chatroom = TeamChatRoom.objects.filter(channel=context.target[1:])
        if chatroom.count() == 0:
            return "I can't seem to find chat room '%s'" % context.target
        chatroom = chatroom.first()

        if context.target != username:
            if TeamChatRoom.objects.filter(
                  channel=context.target[1:],
                  admin__ircnick=context.nick).count() == 0:
                return "You are not '%s' or the admin for %s" % (username, context.target)

        d2 = datetime.now()
        d1 = d2 - timedelta(**{self.units[unit]: int(scale)})
        days = range((d2 - d1).days + 1)
        count = 0
        
        for x, dt in enumerate([d1 + timedelta(days=x) for x in days]):
            log_file = TeamChannels.get_log(chatroom, dt)
            if os.path.isfile(log_file):
                dt_time = dt.time() if x == 0 else None
                count += self.redact(log_file, username, dt_time)

        return "Redacted %d log lines" % count

    def redact(self, log_file, username, dt_time):
        """Redact from log_file, this username from this time onwards"""
        count = 0
        new_file = log_file[:-3] + 'bak'
        with open(log_file, 'r') as readfh:
            with open(new_file, 'w') as writefh:
                for line in readfh:
                    (r, t, u, msg) = line.split('|', 3)
                    if r != 'A' or u != username or (dt_time and t < str(dt_time)):
                        writefh.write(line)
                    else:
                        count += 1
                        writefh.write("R" + line[1:])

        os.rename(new_file, log_file)
        return count

