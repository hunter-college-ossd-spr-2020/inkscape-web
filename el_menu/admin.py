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
Administration of menu items.
"""

from django.utils.translation import get_language
from django.contrib.admin import ModelAdmin, TabularInline, site
from .models import MenuItem, MenuTranslation

class TranslationsInline(TabularInline):
    """Show MenuItems in a stacked tab interface"""
    model = MenuTranslation
    extra = 1

class MenuItemAdmin(ModelAdmin):
    """Each menu item in the admin interface"""
    list_display = ('name', 'url', 'parent', 'lang', 'is_translated', 'category', 'title', 'cms_id')
    search_fields = ('name', 'url', 'title', 'cms_id')
    list_filter = ('lang', 'category')
    raw_id_fields = ('parent',)
    inlines = (TranslationsInline,)

    def is_translated(self, obj):
        """Returns true if this is translated into one's selected language"""
        return self and bool(obj.translations.filter(language=get_language()))
    is_translated.boolean = True
    is_translated.short_description = get_language

site.register(MenuItem, MenuItemAdmin)
