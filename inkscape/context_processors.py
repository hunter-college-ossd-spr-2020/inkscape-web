#
# Copyright 2012, Martin Owens <doctormo@gmail.com>
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

import sys
import email
import django
import logging

from os.path import isfile, join
from collections import OrderedDict
from menus.utils import DefaultLanguageChanger
from django.conf import settings

def tracker_data(request):
    return {
      'TRACKER_URL': getattr(settings, 'PIWIK_URL', None),
      'TRACKER_API_KEY': getattr(settings, 'PIWIK_API_KEY', None),
      'TRACKER_SIDE_ID': getattr(settings, 'PIWIK_SIDE_ID', 1),
    }

def englishslug(request):
    if hasattr(request, "_language_changer"):
        try:
            url = request._language_changer("en")
        except NoReverseMatch:
            url = DefaultLanguageChanger(request)("en")
    else:
        # use the default language changer
        url = DefaultLanguageChanger(request)("en")
    url_parts = url.split('/')
    return {
        'englishslug': url_parts[len(url_parts)-2],
    }

PATH = settings.PROJECT_PATH
INKSCAPE_VERSION = ''
WEBSITE_VERSION = ''
WEBSITE_REVISION = ''
DONATE_NOW = False

VERSION_FILE = join(PATH, 'version')
if isfile(VERSION_FILE):
    emai_msg = email.message_from_file(open(VERSION_FILE))
    WEBSITE_VERSION = emai_msg["version"]
    INKSCAPE_VERSION = emai_msg["inkscape"]
    DONATE_NOW = emai_msg.get("donate", None)

REVISION_FILE = join(PATH, 'data', 'revision')
if isfile(REVISION_FILE):
    with open(REVISION_FILE, 'r') as fhl:
        WEBSITE_REVISION = fhl.read().strip()

def version(request):
    return {
      'DONATE_NOW': DONATE_NOW,
      'INKSCAPE_VERSION': INKSCAPE_VERSION,
      'WEBSITE_REVISION': WEBSITE_REVISION,
      'WEBSITE_VERSION': WEBSITE_VERSION,
      'DJANGO_VERSION': django.get_version(),
      'PYTHON_VERSION': sys.version.split()[0]
    }

