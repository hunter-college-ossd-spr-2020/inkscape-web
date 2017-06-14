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
import time
import atexit
import threading

from importlib import import_module
from easyirc.client.bot import BotClient

from django.db import connection
from django.db.utils import OperationalError

from django.apps import apps
from django.conf import settings

from django.utils import translation
from django.utils.translation import ugettext as _
from django.utils.module_loading import module_has_submodule

from inkscape.models import HeartBeat

from .base import BotCommand, FallbackResponse

class InkscapeBot(object):
    def __init__(self, *args):
        pass

    def run(self):
        HeartBeat.objects.filter(name="ircbot").delete()
        self.beat = HeartBeat.objects.create(name="ircbot")

        self.client = BotClient()
        self.commands = list(self.load_irc_modules())
        self.client.start()
        self.connection = self.client.connections[0]

        self.log_status("Server Started!", 0)
        drum = 2 # wait for two seconds after connecting
        knel = 200 # wait 20 seconds before term and join on error.

        while True:
            try:
                time.sleep(drum)
                self.beat.save()
                assert(self.connection.socket.connected)
                self.ready_commands()
                drum = 60 # wait for a minute for the next heartbeat
            except KeyboardInterrupt:
                self.client.quit()
                for x, conn in enumerate(self.client.connections):
                    if conn.socket.connected:
                        conn.socket.disconnect()
                self.log_status("Keyboard Interrupt", 1)
                drum = 0.1
            except AssertionError as err:
                threads = [t for t in threading.enumerate() if t.name != 'MainThread' and t.isAlive()]
                for t in threads:
                    # This is for error tracking when treading is messed up
                    self.log_status("Thread Locked: %s (Alive:%s, Daemon:%s)\n%s" % (t.name, t.isAlive(), t.isDaemon(), str(err)), -10)
                    knel -= 1
                    if knel < 0:
                        t.terminate()
                        t.join()

                if not threads:
                    self.log_status("Socket Disconnected", -1)
                    break
                else:
                    drum = 0.1

    def log_status(self, msg, status=-1):
        if self.beat.status == 0:
            self.beat.error = msg
            self.beat.status = status
            self.beat.save()

    def load_irc_modules(self):
        """Generate all BotCommands available in all installed apps"""
        for command in self.load_irc_commands(globals(), 'inkscape.management.commands.ircbot'):
            yield command

        for app_config in apps.app_configs.values():
            app = app_config.module
            if module_has_submodule(app, 'irc_commands'):
                app = app.__name__
                module = import_module("%s.%s" % (app, 'irc_commands'))
                for command in self.load_irc_commands(module.__dict__, module.__name__):
                    yield command

    def load_irc_commands(self, possible, mod):
        """See if this is an item that is a Bot Command"""
        self.client.events.msgregex.hookback(".")(FallbackResponse)
        for (name, value) in possible.items():
            if type(value) is type(BotCommand) and \
                 issubclass(value, BotCommand) and \
                 value is not BotCommand and \
                 value.__module__ == mod:
                yield self.register_command(value(self))

    def register_command(self, command):
        """Register a single command class inheriting from BotCommand"""
        print "Hooking up: %s" % command.name
        regexes = command.regex
        if not isinstance(regexes, (list, tuple)):
            regexes = [regexes]
        for regex in regexes:
            self.client.events.msgregex.hookback(regex)(command)
        return command

    def ready_commands(self):
        """Make commands ready after we know for sure that we're connected"""
        for command in self.commands:
            try:
                if not command.is_ready:
                    command.is_ready = bool(command.ready())
            except Exception as err:
                print "Error getting %s ready: %s" % (command.name, str(err))

