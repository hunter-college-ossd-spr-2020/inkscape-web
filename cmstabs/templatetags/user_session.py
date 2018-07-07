#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
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
Provide cms based session templatetags.
"""

import re
import warnings

from django import template
from django.contrib.gis.geoip import HAS_GEOIP
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ugettext

register = template.Library()

BROWSERS = {
  'cr': ('Chrome', 'Chromium'),
  'ff': 'Firefox',
  'sf': 'Safari',
  'ie': ('Internet Explorer', 'IE'),
  'op': 'Opera',
  'kq': 'Konqueror',
  '-' : 'Unknown Browser',
}
DEVICES = {
  'gnu': ('Unknown Gnu/Linux', 'Linux', 'X11', {
    'ubu': ('Ubuntu', 'buntu'),
    'deb': 'Debian',
    'rpm': 'Fedora',
    'ach': 'ARCH',
    'sls': 'Slackware',
    'sus': ('SuSE', 'SUSE'),
    'gen': ('Gentoo', 'gentoo'),
  }),
  'bsd': 'BSD',
  'win': ('Unknown Windows', 'Windows', 'NT', {
    'nt': ('Windows NT Server', 'NT 4.0'),
    'xp': ('Windows XP',    'NT 5.1'),
    'vi': ('Windows Vista', 'NT 6.0'),
    'w7': ('Windows 7',     'NT 6.1'),
    'w8': ('Windows 8',     'NT 6.2', 'NT 6.3'),
  }),
  'and': 'Android',
  'ios': ('iOS', 'iPhone', 'iPad'),
  'osx': ('Mac OS X', 'Macintosh', 'Darwin'),
  '-':   'Unknown Device',
}

def get_match(ST, value, default=None, detail=True):
    matched = None
    for _id, matches in ST.items():
        if not isinstance(matches, (list, tuple)):
            matches = (matches,)
        for match in matches:
            if type(match) is dict:
                if matched and detail == True:
                    return get_match(match, value, matched)
            elif match in value:
                matched = (_id, matches[0])
    return matched or default or ('-', ST.get('-', 'Unknown'))


@register.filter
def device(value, detail=True):
    return get_match(DEVICES, value, detail=detail)[1]
@register.filter
def device_id(value, detail=False):
    return get_match(DEVICES, value, detail=detail)[0]

@register.filter
def browser(value, detail=True):
    return get_match(BROWSERS, value, detail=detail)[1]
@register.filter
def browser_id(value, detail=False):
    return get_match(BROWSERS, value, detail=detail)[0]


@register.filter
def location(value):
    """Transform an IP address into an approximate location."""
    if value == '127.0.0.1':
        return "Right here"
    location = geoip() and geoip().city(value)
    if location and location['country_name']:
        if location['city']:
            return '%s, %s' % (location['city'], location['country_name'])
        else:
            return location['country_name']
    return mark_safe('<i>%s</i>' % ugettext('unknown'))

_geoip = None

def geoip():
    global _geoip
    if _geoip is None and HAS_GEOIP:
        from django.contrib.gis.geoip import GeoIP
        try:
            _geoip = GeoIP()
        except Exception as e:
            warnings.warn(str(e))
    return _geoip

