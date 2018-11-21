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
from cms.utils.moderator import use_draft
from cms.utils.conf import get_cms_setting
from menus.models import CacheKey
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
        self.draft_mode_active = use_draft(request)

class MenuShow():
    def __init__(self, language, request):
        self.language = language
        self.request = request
        self.site = Site.objects.get_current(request)

    @property
    def cache_key(self):
        prefix = get_cms_setting('CACHE_PREFIX')

        key = '%sbasic_menu_nodes_%s_%s' % (prefix, self.language[0], self.site.pk)

#        if self.request.user.is_authenticated():
#            key += '_%s_user' % self.request.user.pk

#        if use_draft(self.request):
#            key += ':draft'
#        else:
        key += ':public'
        return key

    @cached_property
    def is_cached(self):
        db_cache_key_lookup = CacheKey.objects.filter(
            key=self.cache_key,
            language=self.language[0],
            site=self.site.pk,
        )
        return db_cache_key_lookup.exists()

    def get_nodes(self):
        return MenuRendererOverloaded(menu_pool, self.request, self.language).get_nodes()

    def populize_lang(self):
        nodes = self.get_nodes()
        lang = self.language[0]
        root = MenuRoot(self.language)
        MenuRoot.objects.all().filter(language = self.language).delete()
        MenuItem.objects.all().filter(root = root).delete()
        root.save()
        counter = 0
        items = []
        if lang == "en":
            pathlang = ""
        else:
            pathlang = "/" + lang + "/"
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
        key = self.cache_key

        cached_nodes = cache.get(key, None)
        
        if cached_nodes and self.is_cached:
            # Only use the cache if the key is present in the database.
            # This prevents a condition where keys which have been removed
            # from the database due to a change in content, are still used.
            return cached_nodes
        self.populize_lang()
        root = MenuRoot(self.language)
        menuitems = MenuItem.objects.filter(root = root)
        menu = []
        for item in menuitems.filter(parent = None):
            submenu = []
            menudict = dict()
            for subitem in menuitems.filter(parent = item):
                submenudict = dict()
                submenudict['url'] = subitem.url
                submenudict['name'] = subitem.name
                submenu.append(submenudict)
            menudict['url'] = item.url
            menudict['name'] = item.name
            if len(submenu) > 0:
                menudict['submenu'] = submenu
            menu.append(menudict)
            
        cache.set(key, menu, get_cms_setting('CACHE_DURATIONS')['menus'])
        
        if not self.is_cached:
            # No need to invalidate the internal lookup cache,
            # just set the value directly.
            self.__dict__['is_cached'] = True
            # We need to have a list of the cache keys for languages and sites that
            # span several processes - so we follow the Django way and share through
            # the database. It's still cheaper than recomputing every time!
            # This way we can selectively invalidate per-site and per-language,
            # since the cache is shared but the keys aren't
            CacheKey.objects.create(key=key, language=self.language[0], site=self.site.pk)

        return menu

