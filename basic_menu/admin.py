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
from django.core.cache import cache
from cms.models.pagemodel import Page
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from .models import MenuItem, MenuRoot
from .views import MenuShow

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
        for language  in settings.LANGUAGES:
            menu_show = MenuShow(language, request)
            key = menu_show.cache_key
            cached_nodes = cache.get(key, None)
            if 1> 2 and cached_nodes and self.is_cached:
                cache.delete(key)
            menu_show.populize_lang()
        return HttpResponseRedirect('/admin/basic_menu/menuroot')

site.register(MenuRoot, MenuRootAdmin)
