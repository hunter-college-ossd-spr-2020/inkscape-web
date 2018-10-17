#!/usr/bin/env python
#
# (c) 2018 - Martin Owens <doctormo@gmail.com>
#
# Licensed as AGPLv3, see LICENSE for details.
#
"""
Open a trail of django errors, generate a key based on their traceback
and sort them by most frequent.
"""

import re
import hashlib
import logging

from datetime import datetime
from django.utils import timezone

import pytz

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
STATES = (
    ('URL', re.compile(r'\[(?P<day>\d{1,2})\/(?P<mon>\w{3})\/(?P<year>\d{4}) (?P<hour>\d{2}):'
                       r'(?P<mint>\d{2}):(?P<sec>\d{2})\] ERROR \[[_\w\.]+:\d+] '
                       r'Internal Server Error: (?P<url>[\w\/]+)')),
    ('OTHER', re.compile(r'During handling of the above exception, another exception occurred:')),
    ('FIXED', re.compile(r'Traceback \(most recent call last\):')),
    ('FILE', re.compile(r'  File \"(?P<fn>[<>\w\/\-\. ]+)\", line (?P<line>\d+)'
                        r', in (?P<func>[<>\w\/\-\._]+)')),
    ('LINE', re.compile(r'    (?P<line>.+)')),
    ('ERR', re.compile(r'(?P<err>.*(Error|Exception|\.exceptions\.).*)')),
    ('CONT', re.compile(r'(?P<line>.*)')),
)

def get_datetime(day, mon, year, hour, mint, sec, **_): # pylint: disable=too-many-arguments
    """Process the time stamp into a real datetime"""
    month = MONTHS.index(mon) + 1
    return datetime(int(year), month, int(day),
                    int(hour), int(mint), int(sec),
                    tzinfo=pytz.timezone(timezone.get_default_timezone_name()))

def get_line_state(line, allowed, x=0):
    """Return the lines current state (it's type) and the data parsed."""
    # Ignore empty lines
    if not line.strip():
        return (None, None)
    found = []
    for sta, rex in STATES:
        mat = rex.match(line)
        if mat:
            if sta not in allowed:
                found.append(sta)
                continue
            return sta, mat.groupdict()
    if found:
        logging.warning("Unexpected line type %s (expected %s): line: %d", found, allowed, x)
    else:
        logging.error("Unknown line: %s", line)
    return (None, None)

def parse_stream(stream):
    """Parse the given stream for errors and yield as we find them"""
    allowed = ('URL',)
    item = {}
    for x, line in enumerate(stream):
        (state, data) = get_line_state(line.rstrip(), allowed, x=x)

        if state == 'URL':
            allowed = ('FIXED',)
            if item:
                key = tuple(tb['fn'] + ':' + tb['line'] for tb in item['traceback'])
                key = '|'.join(key).encode('utf-8')
                item['key'] = hashlib.md5(key).hexdigest()[:255]
                yield item
            item = {
                'url': data['url'],
                'datetime': get_datetime(**data),
                'traceback': [],
                'error': []
            }
        elif state == 'FIXED':
            allowed = ('FILE',)
        elif state == 'OTHER':
            allowed = ('FIXED',)
        elif state == 'FILE':
            allowed = ('LINE', 'FILE')
            item['traceback'].append(data)
        elif state == 'LINE':
            allowed = ('URL', 'FILE', 'ERR', 'OTHER', )
            item['traceback'][-1]['content'] = data['line']
        elif state == 'ERR':
            allowed = ('URL', 'CONT', 'OTHER')
            item['error'] = [data['err']]
        elif state == 'CONT':
            allowed = ('URL', 'CONT', 'OTHER')
            item['error'].append(data['line'])
