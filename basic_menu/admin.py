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

from django.utils.safestring import mark_safe

from django.contrib.admin import ModelAdmin, site

from inkscape.templatetags.inkscape import timetag_filter

from cms.models.pagemodel import Page


from .models import MenuItem, Menu

BOLD = "<strong style='display: block; width: 98%%; padding: 6px; color: white; background-color: %s;'>%s</strong>"

class MenuItemAdmin(ModelAdmin):
    list_display = ('name', 'url', 'language', 'parent', 'order')
    
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
                menuitem.name = page.title(language)
                menuitem.orden = root_counter
                menuitem.language = language
                menuitem.save()
                child_counter = 0
                for subpage in page.get_descendants():
                    child_counter += 1
                    submenuitem = MenuItem()
                    submenuitem.parent = menuitem
                    submenuitem.url = subpage.get_absolute_url(language)
                    submenuitem.name = page.title(language)
                    submenuitem.orden = child_counter
                    submenuitem.language = language
                    submenuitem.save()

site.register(MenuItem, MenuItemAdmin)
