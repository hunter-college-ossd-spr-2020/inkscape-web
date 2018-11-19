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
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import NoReverseMatch, reverse, resolve
from django.utils.functional import cached_property
from cms.models.pagemodel import Page



from django.db.models import (
    Model, Manager, CharField, URLField, IntegerField, ForeignKey
)

class Menu(Manager):
    def __init__(self): #, request):
        #self.request = request
        self.language = "en" #self.request.LANGUAGE_CODE
        
    def show_level(self, parent):
        self.filter(language = self.language).filter(parent = parent).order_by('order')
    
    @property
    def cache_key(self):
        prefix = get_cms_setting('CACHE_PREFIX')
        key = '%smenu_code_%s' % (prefix, self.language)
        key += ':public'
        return key

    @cached_property
    def is_cached(self):
        db_cache_key_lookup = CacheKey.objects.filter(
            key=self.cache_key,
            language=self.language
        )
        return db_cache_key_lookup.exists()

    def show_menu(self):
        populize_menu()
        key = self.cache_key
        cached_menu = cache.get(key, None)
        if cached_menu and self.is_cached:
            # Only use the cache if the key is present in the database.
            # This prevents a condition where keys which have been removed
            # from the database due to a change in content, are still used.
            return cached_menu
        menu = {}
        for item in show_level(self, NULL):
            submenu = {}
            for subitem in showLevel(self, language, item):
                submenu[url] = subitem.url
                submenu[name] = subitem.title
            menu[url] = item.url
            menu[name] = item.title
            menu[sumenu] = submenu
        cached_menu = render_to_string('menu.html', menu)
        cache.set(key, cached_menu, get_cms_setting('CACHE_DURATIONS')['menus'])

        if not self.is_cached:
            # No need to invalidate the internal lookup cache,
            # just set the value directly.
            self.__dict__['is_cached'] = True
            # We need to have a list of the cache keys for languages and sites that
            # span several processes - so we follow the Django way and share through
            # the database. It's still cheaper than recomputing every time!
            # This way we can selectively invalidate per-site and per-language,
            # since the cache is shared but the keys aren't
            CacheKey.objects.create(key=key, language=self.language)  
        return cached_menu

    def populize_menu(self):
        #TODO: clear all
        for language  in settings.LANGUAGES:
            cms_pages = Page.objects.public()
            root_counter = 0
            for page in cms_pages:
                root_counter += 1
                menuitem = MenuItem()
                menuitem.parent = null
                menuitem.url = page.get_absolute_url(language)
                menuitem.name = page.name(language)
                menuitem.orden = root_counter
                menuitem.language = language
                menuitem.save()
                child_counter = 0
                for subpage in page.get_descendants():
                    child_counter += 1
                    submenuitem = MenuItem()
                    submenuitem.parent = menuitem
                    submenuitem.url = subpage.get_absolute_url(language)
                    submenuitem.name = page.name(language)
                    submenuitem.orden = child_counter
                    submenuitem.language = language
                    submenuitem.save()

class MenuItem(Model):
    """A collection menus"""
    parent = ForeignKey('self', null=True, blank=True)
    url = URLField(help_text="Location of content.", unique=True)
    name = CharField(max_length=128)
    order = IntegerField(default=0)
    language = CharField(max_length=8, choices=settings.LANGUAGES)
    objects = Menu()
