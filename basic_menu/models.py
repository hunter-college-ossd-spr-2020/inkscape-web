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

from django.core.urlresolvers import reverse
from django.conf import settings

from django.db.models import (
    Model, Manager, CharField, IntegerField, ForeignKey
)

class MenuRoot(Model):
    """A whole menu for a language"""
    language = CharField(max_length=12, choices=settings.LANGUAGES, primary_key=True)
    
    def show_menu(self):
        menuitems = MenuItem.objects.filter(root = self)
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
        return menu

    def __str__(self):
        return self.get_language_display()

    def get_absolute_url(self):
        """Return a link to the debug page for menus"""
        return "https://www.inkscape.org"

class MenuItem(Model):
    """A collection menus"""
    root = ForeignKey(MenuRoot, related_name='items')
    parent = ForeignKey('self', null=True, blank=True, related_name='children')
    # This must NOT be a URLField as a URLField is restricted to external
    # fully qualified urls and doesn't accept local page URLs.
    url = CharField(max_length=255, help_text="Location of content.", unique=True)
    name = CharField(max_length=128)
    order = IntegerField(default=0)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the linked content as this items url"""
        return self.url
