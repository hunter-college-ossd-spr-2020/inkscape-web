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
Signals for resources
"""

import logging
from django.db.models import signals
from django.apps import AppConfig
from django.conf import settings

# For clearing the cache in a file
if not settings.DEBUG:
    from inkscape.fastly_cache import FastlyCache

class ResourceConfig(AppConfig):
    name = 'resources'

    @staticmethod
    def clean_tags(*args, **kw):
        """Clean unused tags (effects all, not just tags in the deleted item"""
        from .models import Tag
        Tag.objects.filter(resources__isnull=True, category__isnull=True).delete()

    @staticmethod
    def remove_file(instance, **kw):
        for field in ('download', 'signature', 'checked_sig', 'thumbnail', 'rendering'):
            fn = getattr(instance, field)
            if fn and fn.url and not settings.DEBUG:
                FastlyCache().purge_media(fn)
            try:
                getattr(instance, field).delete(save=False)
            except Exception as err:
                logging.error("IOError: %s\n" % str(err))

    def ready(self):
        from .models import Resource
        signals.post_delete.connect(self.clean_tags, sender=Resource)
        signals.pre_delete.connect(self.remove_file, sender=Resource)

