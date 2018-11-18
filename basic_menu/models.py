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

import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from django.db.models import (
    Model, Manager, CharField, URLField, IntegerField, ForeignKey
)

class Menu(Manager):
    def showLevel(self, language, parent):
        self.filter(language = language).filter(parent = parent).order_by('order')
    
    def showMenu(self, language):
        menu = {}
        for item in showLevel(self, language, NULL):
            submenu = {}
            for subitem in showLevel(self, language, item):
                submenu[url] = subitem.url
                submenu[name] = subitem.name
            menu[url] = item.url
            menu[name] = item.name
            menu[sumenu] = submenu
        return render_to_string('menu.html', menu)

class MenuItem(Model):
    """A collection menus"""
    parent = ForeignKey('self', null=True, blank=True)
    url = URLField(help_text="Location of content.", unique=True)
    name = CharField(max_length=128)
    order = IntegerField(default=0)
    language = CharField(max_length=8, choices=settings.LANGUAGES)
    objects = Menu()
