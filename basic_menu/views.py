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
Basic menu views
"""

from django.utils.functional import cached_property
from django.core.cache import cache
from django.contrib.sites.models import Site
from django.conf import settings

from menus.menu_pool import menu_pool, MenuRenderer

from .models import MenuItem, MenuRoot

class MenuRendererOverloaded(MenuRenderer):
    # The main logic behind this class is to decouple
    # the singleton menu pool from the menu rendering logic.
    # By doing this we can be sure that each request has it's
    # private instance that will always have the same attributes.

    def __init__(self, pool, request, language):
        self.pool = pool
        # It's important this happens on init
        # because we need to make sure that a menu renderer
        # points to the same registered menus as long as the
        # instance lives.
        self.menus = pool.get_registered_menus(for_rendering=True)
        self.request = request
        self.request_language = language
        self.site = Site.objects.get_current(request)
        self.draft_mode_active = False 

class MenuShow():
    def __init__(self, language, request):
        self.language = language
        self.request = request
        self.site = Site.objects.get_current(request)

    @property
    def cache_key(self):
        prefix = getattr(settings, 'MENU_CACHE_PREFIX', 'menu')
        return '%s_%s_%s' % (prefix, self.language[0], self.site.pk)

    @cached_property
    def is_cached(self):
        return cache.get(self.cache_key)

    def get_nodes(self):
        return MenuRendererOverloaded(menu_pool, self.request, self.language[0]).get_nodes()

    def populize_lang(self):
        nodes = self.get_nodes()
        lang = self.language[0]
        if len(lang) == 1: #boring hack one letter root menu added, need to fix
            return
        root = MenuRoot(self.language[0])
        MenuRoot.objects.all().filter(language = self.language).delete()
        MenuItem.objects.all().filter(root = root).delete()
        root.save()
        counter = 0
        items = []
        if lang == "en":
            pathlang = ""
        else:
            pathlang = "/" + lang 
        for node in nodes:
            if node.visible == True:
                item = dict()
                counter += 1
                item['parent'] = node.parent_id
                item['id'] = node.id
                if node.attr and node.attr['redirect_url']:
                    item['url'] = node.attr['redirect_url']
                else:
                    item['url'] = pathlang + node.get_absolute_url()
                
                item['name'] = node.title
                items.append(item)
        root_counter = 0
        for item in items:
            if item['parent'] == None:
                root_counter += 1
                menuitem = MenuItem(
                    parent = None,
                    url = item['url'],
                    name = item['name'],
                    order = root_counter,
                    root = root)
                menuitem.save()
                child_counter = 0
                for subitem in items:
                    if subitem['parent'] == item['id'] and item['parent'] == None:
                        child_counter += 1
                        submenuitem = MenuItem(
                            parent = menuitem,
                            url = subitem['url'],
                            name = subitem['name'],
                            order = child_counter,
                            root = root)
                        submenuitem.save()
                        
    def show_menu(self):
        """Generates the menu as a list of dictionaries and submenu lists"""
        root_menu = cache.get(self.cache_key, None)
        if not root_menu:
            root_menu = self.generate_menu()
            cache.set(self.cache_key, root_menu, getattr(settings, 'MENU_CACHE_DURATION', 300))
        return root_menu

    def generate_menu(self):
        """Generate the menu tree"""
        root_menu = []
        qset = MenuItem.objects.filter(root_id=self.language)
        items = dict((item['pk'], {'item': item, 'submenu': []})
                     for item in qset.values('pk', 'parent', 'name', 'url'))
        items[None] = {'submenu': root_menu}

        for datum in items.values():
            if 'item' in datum:
                items[datum['item']['parent']]['submenu'].append(datum['item'])

        return root_menu
