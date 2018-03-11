#
# Copyright 2015-2017, Martin Owens <doctormo@gmail.com>
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
Starts an irc bot to join the configured IRC channel.
"""

import os
import atexit

from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Starts an irc bot that will join the main channel and interact with the website.'

    def handle(self, *args, **options):
        if not hasattr(settings, 'IRCBOT_PID'):
            print "Please set IRCBOT_PID to a file location to enable bot."
            return

        if not hasattr(settings, 'CONNECTIONS'):
            print "Please set CONNECTIONS to the IRC setup needed."
            return

        from ircbot.bot import InkscapeBot

        with open(settings.IRCBOT_PID, 'w') as pid:
            pid.write(str(os.getpid()))
        atexit.register(lambda: os.unlink(settings.IRCBOT_PID))
        # XXX Filter options and pass into bot
        InkscapeBot().run()

