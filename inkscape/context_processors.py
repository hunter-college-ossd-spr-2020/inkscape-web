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

import os
import sys
import email
from datetime import date

import django
from django.conf import settings
from django.utils.timezone import now

def tracker_data(request):
    """Add tracker data for Piwik to template"""
    return {
        'TRACKER_URL': getattr(settings, 'PIWIK_URL', None),
        'TRACKER_API_KEY': getattr(settings, 'PIWIK_API_KEY', None),
        'TRACKER_SIDE_ID': getattr(settings, 'PIWIK_SIDE_ID', 1),
    }

PATH = settings.PROJECT_PATH
WEBSITE_VERSION = ''
WEBSITE_REVISION = ''

def proc_date(d):
    if d and '-' in d and len(d) == 10:
        try:
            year, mm, dd = d.strip().split('-')
            return date(int(year), int(mm), int(dd))
        except:
            return None
    return None

VERSION_FILE = os.path.join(PATH, 'version')
if os.path.isfile(VERSION_FILE):
    MSG = email.message_from_file(open(VERSION_FILE))
    WEBSITE_VERSION = str(MSG["version"])

REVISION_FILE = os.path.join(PATH, 'data', 'revision')
if os.path.isfile(REVISION_FILE):
    with open(REVISION_FILE, 'r') as fhl:
        WEBSITE_REVISION = fhl.read().strip()

def version(request):
    """Return useful version information to templates"""
    today = now().date()
    return {
        'RENDER_TIME': now(),
        'WEBSITE_REVISION': WEBSITE_REVISION,
        'WEBSITE_VERSION': WEBSITE_VERSION,
        'DJANGO_VERSION': django.get_version(),
        'PYTHON_VERSION': sys.version.split()[0]
    }
