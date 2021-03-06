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
Dealing with fastly caches.
"""

import os
import sys
import ssl
import time
import logging

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.templatetags.static import static

try:
    import fastly
except ImportError:
    logging.warning("No fastly module installed (skipping)")
    fastly = None

# Because python2.7 broke SSL for many computers.
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

def touch(fname, times=None):
    """Unix like touching of files"""
    with open(fname, 'a'):
        os.utime(fname, times)

KEY = 'FASTLY_CACHE_API_KEY'
SERVICE = 'FASTLY_CACHE_SERVICE'

class FastlyCache(object):
    """Control a fastly cache, uses default settings if available"""

    def __init__(self, *args, **kwargs):
        self.key = kwargs.get('key', getattr(settings, KEY, None))
        self.service = kwargs.get('service', getattr(settings, SERVICE, None))
        self.api = None
        if fastly is not None and self.key is not None:
            self.api = fastly.API()
            self.api.authenticate_by_key(self.key)

    def clean_static(self, old=False):
        """
          Purge all new static files from cache,

          purge old ones too if old=True (all static files)
        """
        if not os.path.isdir(settings.STATIC_ROOT):
            return sys.stderr.write("\nStatic directory doesn't exist or is "
                "empty. Have you run collectstatic yet?\n\n")

        for path in self.clean_dir(settings.STATIC_ROOT, old=old, label='Static'):
            # We don't want to just use get static url, because that just points
            # back to fastly cache which is not what we need for this api
            self.purge(static(path))

    def clean_media(self, old=False):
        """Like clean_static but for media files"""
        if not os.path.isdir(settings.MEDIA_ROOT):
            return sys.stderr.write("\nMedia directory doesn't exist or is "
                "empty. Do you have any media files yet?\n\n")

        for path in self.clean_dir(settings.MEDIA_ROOT, old=old, label='Media'):
            self.purge(os.path.join(settings.MEDIA_URL, path))

    def clean_dir(self, root, old=False, label=''):
        """
        Returns all files that have changed since the last .fastly_cache was created
        """
        last_clear = 0
        last_file = os.path.join(root, '.fastly_cleared')
        if os.path.isfile(last_file):
            last_clear = os.path.getmtime(last_file)
            print("\nLast cache clear: {}\n".format(time.ctime(last_clear)))
        else:
            print("\nNever cleared before (first run)\n")

        count = 0
        cleared = 0

        for name, _, files in os.walk(root, topdown=False):
            for fname in files:
                path = os.path.join(name, fname)
                if path == last_file:
                    continue
                count += 1

                if old or os.path.getmtime(path) > last_clear:
                    cleared += 1
                    yield path.replace(root, '').lstrip('/')

        print("\n  * {:d} of {:d} {} files cleared\n\n".format(cleared, count, label))
        if not count:
            print("There weren't any {} files, run collectstatic.".format(label))

        if cleared:
            touch(last_file)

    def purge_key(self, key):
        """Take an object key and ask the content to be refreshed"""
        if self.api is None:
            #sys.stderr.write("No-cache: key %s -> %s\n" % (self.service, key))
            return False
        try:
            return self.api.purge_key(self.service, key)
        except Exception as err:
            logging.error("Couldn't purge key, %s" % str(err))
            return False

    def purge_media(self, field):
        """Takes a file field and purges the media url"""
        if not hasattr(field, 'url'):
            raise ValueError("Can not purge media field, not a field")
        self.purge(field.url)

    def purge(self, url):
        """Purge any static or media file from the fastly cache"""

        if '://' in url:
            (domain, location) = url.split('://', 1)[-1].split('/', 1)
        else:
            domain = get_current_site(None).domain
            location = url.lstrip('/')

        var = (url, domain, location)
        if self.api is None:
            sys.stderr.write("No-cache: purging %s -> %s/%s (ignored)\n" % var)
            return False

        try:
            return self.api.purge_url(domain, '/' + location)
        except Exception:
            sys.stderr.write("Error: purging %s -> %s/%s (ignored)\n" % var)
