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
from django.conf.urls import include, url
from cms.models.pagemodel import Page
from django.conf import settings
from .models import MenuItem, MenuRoot

class NestableTabularInline(TabularInline):
    class Media:
        js = ('js/jquery.nestable.js', 'js/admin.nestable.js')


class MenuItemsInline(NestableTabularInline):
    """Show MenuItems in a stacked tab interface"""
    model = MenuItem
    extra = 1

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
            root = MenuRoot(lang)
            root.save()
            cms_pages = Page.objects.public()
            root_counter = 0
            for page in cms_pages:
                if page.soft_root == 0:
                    root_counter += 1
                    menuitem = MenuItem()
                    menuitem.parent = None
                    menuitem.id = page.id
                    menuitem.url = page.get_absolute_url(lang)
                    menuitem.name = page.get_menu_title(lang)
                    menuitem.orden = root_counter
                    menuitem.root = root
                    menuitem.save()
                    child_counter = 0
                    for subpage in cms_pages:
                        if subpage.soft_root == page.id:
                            child_counter += 1
                            submenuitem = MenuItem()
                            submenuitem.parent = menuitem
                            submenuitem.url = subpage.get_absolute_url(lang)
                            submenuitem.name = page.get_menu_title(lang)
                            submenuitem.id = page.id
                            submenuitem.orden = child_counter
                            submenuitem.root = root
                            submenuitem.save()
        return HttpResponseRedirect('/admin/basic_menu/')

site.register(MenuRoot, MenuRootAdmin)
