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
Provide useful tools for showing svg file in the templates directly.
"""
from datetime import datetime

from django.template import Library
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date, parse_time

register = Library() #pylint: disable=invalid-name

def _datetime(dtime):
    """Forces a variable to be a datetime (not date or time)"""
    now = datetime.now(timezone.utc)
    if isinstance(dtime, str):
        if ' ' in dtime or 'T' in dtime:
            dtime = parse_datetime(dtime)
        elif '-' in dtime:
            dtime = parse_date(dtime)
        elif ':' in dtime:
            dtime = parse_time(dtime)
        else:
            raise ValueError("Should be a datetime object, got string: %s" % dtime)
    if not isinstance(dtime, datetime) or not dtime.tzinfo:
        return datetime(
            getattr(dtime, 'year', now.year),
            getattr(dtime, 'month', now.month),
            getattr(dtime, 'day', now.day),
            getattr(dtime, 'hour', 0),
            getattr(dtime, 'minute', 0),
            getattr(dtime, 'second', 0),
            getattr(dtime, 'microsecond', 0),
            timezone.utc)
    return dtime or now


@register.filter("timedelta")
def _timedelta(dtime, other=None):
    """Returns the clean timedelta for this dt, other can be any date/time or None for now()"""
    return _datetime(other) - _datetime(dtime)

@register.filter("totalseconds")
def totalseconds(dtime, other=None):
    """Return the number of seconds in this delta, can be positive or negative"""
    return _timedelta(dtime, other).total_seconds()
