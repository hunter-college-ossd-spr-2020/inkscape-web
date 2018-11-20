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
from django.db.models.query import Prefetch, prefetch_related_objects
from django.conf.urls import include, url
from cms.models.pagemodel import Page
from cms.utils.conf import get_cms_setting
from cms.utils.conf import get_languages
from cms.cms_menus import CMSMenu, get_menu_node_for_page
from cms.utils.page import get_page_queryset
from menus.menu_pool import menu_pool, Menu
from cms.cms_menus import get_visible_nodes
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from cms.models import EmptyTitle
from .models import MenuItem, MenuRoot
from cms.utils.i18n import (
    get_fallback_languages,
    get_public_languages,
    hide_untranslated,
    is_valid_site_language,
)
import logging

logger = logging.getLogger(__name__)

class NestableTabularInline(TabularInline):
    class Media:
        js = ('js/jquery.nestable.js', 'js/admin.nestable.js')


class MenuItemsInline(NestableTabularInline):
    """Show MenuItems in a stacked tab interface"""
    model = MenuItem
    extra = 1

class MenuCustom(Menu):

    def get_nodes(self, request, language):
        from cms.models import Title

        site = self.renderer.site
        lang = language[0]
        pages = get_page_queryset(
            site,
            draft=self.renderer.draft_mode_active,
            published=not self.renderer.draft_mode_active,
        )

        _valid_language = True
        _hide_untranslated = False

        languages = [lang]

        pages = (
            pages
            .filter(title_set__language__in=languages)
            .select_related('node')
            .order_by('node__path')
            .distinct().published()
        )
        print(pages)

        if not self.renderer.draft_mode_active:
            # we're dealing with public pages.
            # prefetch the draft versions.
            pages = pages.select_related('publisher_public__node')
        pages = get_visible_nodes(request, pages, site)

        if not pages:
            return []

        try:
            homepage = [page for page in pages if page.is_home][0]
        except IndexError:
            homepage = None

        titles = Title.objects.filter(
            language__in=languages,
            publisher_is_draft=self.renderer.draft_mode_active,
        )

        lookup = Prefetch(
            'title_set',
            to_attr='filtered_translations',
            queryset=titles,
        )

        #if DJANGO_1_9:
            # This function was made public in django 1.10
            # and as a result its signature changed
        #prefetch_related_objects(pages, [lookup])
        #else:
        prefetch_related_objects(pages, lookup)

        # Build the blank title instances only once
        blank_title_cache = {language: EmptyTitle(language=language) for language in languages}

        if lang not in blank_title_cache:
            blank_title_cache[lang] = EmptyTitle(language=lang)

        # Maps a node id to its page id
        node_id_to_page = {}

        def _page_to_node(page):
            # EmptyTitle is used to prevent the cms from trying
            # to find a translation in the database
            page.title_cache = blank_title_cache.copy()

            for trans in page.filtered_translations:
                page.title_cache[trans.language] = trans
            menu_node =  get_menu_node_for_page(
                self.renderer,
                page,
                lang,
                None
            )
            menu_node.lang = lang
            return menu_node

        menu_nodes = []

        for page in pages:
            node = page.node
            parent_id = node_id_to_page.get(node.parent_id)

            if node.parent_id and not parent_id:
                # If the parent page is not available (unpublished, etc..)
                # don't bother creating menu nodes for its descendants.
                continue

            menu_node = _page_to_node(page)
            cut_homepage = homepage and not homepage.in_navigation

            if cut_homepage and parent_id == homepage.pk:
                # When the homepage is hidden from navigation,
                # we need to cut all its direct children from it.
                menu_node.parent_id = None
            else:
                menu_node.parent_id = parent_id
            node_id_to_page[node.pk] = page.pk
            menu_nodes.append(menu_node)
        return menu_nodes


menu_pool.register_menu(MenuCustom)

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
        MenuItem.objects.all().delete()
        MenuRoot.objects.all().delete()
        for language  in settings.LANGUAGES :
            lang = language[0]
            menupool = menu_pool.get_renderer(request)
            nodes = menupool.get_menu('MenuCustom').get_nodes(request, language)
            root = MenuRoot(lang)
            root.save()
            counter = 0
            items = []
            for node in nodes:
                if node.path != "" and node.lang == lang:
                    item = dict()
                    counter += 1
                    item['parent'] = node.parent_id
                    item['id'] = node.id
                    item['url'] = node.lang + "/" + node.path
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
        return HttpResponseRedirect('/admin/basic_menu/menuroot/')

site.register(MenuRoot, MenuRootAdmin)

