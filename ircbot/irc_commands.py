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
Commands related to Users and Teams
"""

from datetime import timedelta, datetime
from ircbot.base import BotCommand


class LogChannel(BotCommand):
    def __call__(self, context, message, *args, **kwargs):
        """Call for any message to this channel, it won't consume the message"""
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

