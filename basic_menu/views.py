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

import json, sys

from django.views.generic import UpdateView, DetailView, ListView, RedirectView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.http import request
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse, resolve
from django.utils.functional import cached_property
from cms.models.pagemodel import Page
from .models import MenuItem, Menu

from django.db.models import (
    Model, Manager, CharField, URLField, IntegerField, ForeignKey
)

#class ShowMenu():

#    def __init__(self):
#        self.lenguage = self.request.LANGUAGE_CODE

@property
def cache_key(self):
    prefix = 'CACHE'
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

def show_menu():
#    key = cache_key
#    cached_menu = cache.get(key, None)
#    if cached_menu and self.is_cached:
#        # Only use the cache if the key is present in the database.
#        # This prevents a condition where keys which have been removed
#        # from the database due to a change in content, are still used.
#        return render_to_response('menu.html', cached_menu)
    menu = {}
    mymenu = Menu();
    print >>sys.stderr, 'Goodbye, cruel world!'
    for item in mymenu.get_children("en",mymenu.get_root("en")):
        submenu = {}
        for subitem in mymenu.get_children("en", item):
            submenu[url] = subitem.url
            submenu[name] = subitem.name
        menu[url] = item.url
        menu[name] = item.name
        menu[sumenu] = submenu
#    cached_menu = render_to_response('basic_menu/menu.html', menu)
#    cache.set(key, cached_menu, get_cms_setting('CACHE_DURATIONS')['menus'])

#    if not self.is_cached:
#        # No need to invalidate the internal lookup cache,
#        # just set the value directly.
#        self.__dict__['is_cached'] = True
#        # We need to have a list of the cache keys for languages and sites that
#        # span several processes - so we follow the Django way and share through
#        # the database. It's still cheaper than recomputing every time!
#        # This way we can selectively invalidate per-site and per-language,
#        # since the cache is shared but the keys aren't
#        CacheKey.objects.create(key=key, language=self.language)  
    render_to_string('basic_menu/menu.html', {'menu_items': menu})
