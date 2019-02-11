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
Cleans the static files from a fastly cache
"""
from django.core.management import BaseCommand
from inkscape.fastly_cache import FastlyCache

class Command(BaseCommand):
    """Clear fastly cache based on last clear and modified times"""
    help = __doc__

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--url', '-u', default=[], action='append',
            dest='urls', help='Only invalidate this url.')

    def handle(self, urls=(), *args, **options):
        cache = FastlyCache()
        if urls:
            for url in urls:
                print("Purging: {}".format(url))
                cache.purge(url)
        else:
            cache.clean_static()
            cache.clean_media()
