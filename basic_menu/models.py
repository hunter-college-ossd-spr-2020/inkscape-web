#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
# Copyright 2018, Jabiertxo Arraiza <jabiertxof@gmail.com>
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
Basic menu are a custom app to show inkscape menu.
"""

import json

from django.conf import settings
from cms.models.pagemodel import Page

from django.db.models import (
    Model, Manager, CharField, URLField, IntegerField, ForeignKey
)


class Menu(Manager):
    """A collection menus"""
    
#    @property
#    def cache_key(self):
#        prefix = 'CACHE'
#        key = '%smenu_code_%s' % (prefix, self.language)
#        key += ':public'
#        return key

#    @cached_property
#    def is_cached(self):
#        db_cache_key_lookup = CacheKey.objects.filter(
#            key=self.cache_key,
#            language=self.language
#        )
#        return db_cache_key_lookup.exists()
    
    def get_children(self, language, parent):
        return self.filter(language = language).filter(parent = parent).order_by('order')

    def get_root(self):
        return self.filter(url = "https://www.inkscape.org")
    
    def get_menu(self, language):
#        key = cache_key
#        cached_menu = cache.get(key, None)
#        if cached_menu and self.is_cached:
#            # Only use the cache if the key is present in the database.
#            # This prevents a condition where keys which have been removed
#            # from the database due to a change in content, are still used.
#            return cached_menu
        root = self.get_root()
        for item in self.get_children(lenguage, root):
            submenu = {}
            for subitem in self.get_children(lenguage, item):
                submenu[url] = subitem.url
                submenu[name] = subitem.name
            menu[url] = item.url
            menu[name] = item.name
            menu[submenu] = submenu
        cached_menu = menu
#        cache.set(key, cached_menu, get_cms_setting('CACHE_DURATIONS')['menus'])
#        if not self.is_cached:
#            # No need to invalidate the internal lookup cache,
#            # just set the value directly.
#            self.__dict__['is_cached'] = True
#            # We need to have a list of the cache keys for languages and sites that
#            # span several processes - so we follow the Django way and share through
#            # the database. It's still cheaper than recomputing every time!
#            # This way we can selectively invalidate per-site and per-language,
#            # since the cache is shared but the keys aren't
#            CacheKey.objects.create(key=key, language=language) 
        return cached_menu


class MenuItem(Model):
    """A collection menus"""
    parent = ForeignKey('self', null=True, blank=True)
    url = URLField(help_text="Location of content.", unique=True)
    name = CharField(max_length=128)
    order = IntegerField(default=0)
    language = CharField(max_length=8, choices=settings.LANGUAGES)
    objects = Menu()
