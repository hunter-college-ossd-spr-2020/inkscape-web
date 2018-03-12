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

def url(item):
    """Returns the full URL"""
    if hasattr(item, 'get_absolute_url'):
        item = item.get_absolute_url()
    return settings.SITE_ROOT.rstrip('/') + unicode(item)

class BotCommand(object):
    """Base class for all commands you want available in irc"""
    LANGS = [l[0] for l in settings.LANGUAGES]
    is_channel = True
    is_direct = True
    automatic = True
    regex = []

    @property
    def name(self):
        return type(self).__name__

    @property
    def connection(self):
        return self.caller.connection

    def run_command(self, *args, **kwargs):
        """Called when the regex matches from inputs"""
        raise NotImplementedError("run_command in %s" % type(self).__name__)

    def ready(self):
        """Called when the connection is ready"""
        return True

    def __init__(self, caller):
        self.is_ready = False
        self.caller = caller
        self.client = caller.client
        self.context = None
        if not hasattr(self.caller, 'consumed'):
            self.caller.consumed = False

    def get_language(self):
        """Pick the best language to reply with here, default is 'en'"""
        return 'en'

    def __call__(self, context, message, *args, **kwargs):
        """Some basic extra filtering for directed commands"""
        self.context = context
        is_channel = context.target and context.target.startswith('#')
        if not self.is_channel and is_channel:
            print " ! %s does not accept messages in channel." % self.name
            return False

        if not self.is_direct and (not is_channel \
             or message.startswith(self.nick + ':') \
             or message.endswith(self.nick)
           ):
            print " ! %s does not expect direct message from '%s'." % (self.name, context.ident.nick)
            return False

        connection.close_if_unusable_or_obsolete()

        try:
            translation.activate(self.get_language())
            ret = self.run_command(context, *args, **kwargs)
            if isinstance(ret, bool):
                self.caller.consumed |= ret
                return None
            elif isinstance(ret, (str, unicode)):
                self.caller.consumed = True
                return ret
            else:
                raise ValueError("Command '%s' should return True/False or a string" % self.name)

        except OperationalError as error:
            if 'gone away' in str(error):
                return "The database is being naughty, reconnecting..."
            else:
                return "A database error, hmmm."
        except Exception:
            if context:
                context.connection.privmsg(context.target, "There was an error")
            raise

    @property
    def nick(self):
        return self.client.connections[0].tried_nick


class FallbackResponse(BotCommand):
    """Returns a standard response when the command wasn't consumed"""
    is_channel = False
    automatic = False
    regex = "(.+)"

    def run_command(self, context, message):
        print(">>> {}".format(message))
        return False


class ExitCommand(BotCommand):
    name = "Exit the IRC Bot"
    regex = """The trouble with having an open mind, of course, is that people will insist on coming along and trying to put things in it."""

    def run_command(self, context):
        if context and context.ident:
            self.caller.log_status("Told to quit by: " + context.ident.nick, 2)
        try:
            self.client.quit()
        except Exception as error:
            print "Error quitting: %s" % str(error)

class HelloCommand(BotCommand):
    regex = [
      "Hello", "Allo", "Bonjour",
    ]
    def run_command(self, context):
        return _("Hello there %(nick)s") % {'nick': context.ident.nick}

class DumpCommand(BotCommand):
    regex = "DumpInfo"
    def run_command(self, context):
        return "Info: " + \
          ', ident:' + context.ident + \
          ', nick:' + context.ident.nick + \
          ', username:' + context.ident.username + \
          ', host:' + context.ident.host + \
          ', msgtype:' + context.msgtype + \
          ', target:' + context.target

