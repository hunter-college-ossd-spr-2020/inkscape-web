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
from django.http import HttpResponseRedirect
from django.contrib.admin import ModelAdmin, TabularInline, site
from django.conf.urls import url
from cms.models.pagemodel import Page
from menus.menu_pool import menu_pool, MenuRenderer
from menus.modifiers import Marker, Level
from django.conf import settings
from .models import MenuItem, MenuRoot
from django.contrib.sites.models import Site
from cms.utils.moderator import use_draft


class MenuItemsInline(TabularInline):
    """Show MenuItems in a stacked tab interface"""
    model = MenuItem
    extra = 1

class MarkerOverloaded(Marker):
    """
    searches the current selected node and marks them.
    current_node: selected = True
    siblings: sibling = True
    descendants: descendant = True
    ancestors: ancestor = True
    """
    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if post_cut or breadcrumb:
            return nodes
        selected = None
        root_nodes = []
        for node in nodes:
            if not hasattr(node, "descendant"):
                node.descendant = False
            if not hasattr(node, "ancestor"):
                node.ancestor = False
            if not node.parent:
                if selected and not selected.parent:
                    node.sibling = True
                root_nodes.append(node)
            if node.selected:
                if node.parent:
                    newnode = node
                    while newnode.parent:
                        newnode = newnode.parent
                        newnode.ancestor = True
                    for sibling in node.parent.children:
                        if not sibling.selected:
                            sibling.sibling = True
                else:
                    for root_node in root_nodes:
                        if not root_node.selected:
                            root_node.sibling = True
                if node.children:
                    self.mark_descendants(node.children)
                selected = node
            if node.children:
                node.is_leaf_node = False
            else:
                node.is_leaf_node = True
        MenuRootAdmin.populize_menu_lang(nodes)
        return nodes


class LevelOverloaded(Level):
    """
    marks all node levels
    """
    post_cut = True

    def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
        if breadcrumb:
            return nodes
        for node in nodes:

            if not node.parent:
                if post_cut:
                    node.menu_level = 0
                else:
                    node.level = 0
                self.mark_levels(node, post_cut)
        MenuRootAdmin.populize_menu_lang(nodes)
        return nodes

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

class MenuRootAdmin(ModelAdmin):
    """Customise the root menu in the admin interface"""
    inlines = (MenuItemsInline,)
    
    def get_urls(self):
        urls = super(MenuRootAdmin, self).get_urls()
        urls.append(url(
                r'menugenerate',
                self.populize_menu,
                name='populize_menu',
            ))
        return urls

    def populize_menu(self, request):
        #TODO: clear all
        for language  in settings.LANGUAGES :
            self.populize_menu_lang(self.get_nodes(request, language, False), language, False)
        return HttpResponseRedirect('/admin/basic_menu/menuroot/')
    
    def get_nodes(self, request, language, redirect):
        lang = language[0]
        pool = menu_pool
        return MenuRendererOverloaded(pool, request, lang).get_nodes()
    
    def populize_menu_lang(self, nodes, language, redirect):
        lang = language[0]
        root = MenuRoot(lang)
        MenuRoot.objects.all().filter(language = language).delete()
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
        if redirect:
            return HttpResponseRedirect('/admin/basic_menu/menuroot/')
        
site.register(MenuRoot, MenuRootAdmin)

