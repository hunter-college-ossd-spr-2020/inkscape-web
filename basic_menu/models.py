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
from cms.models.pagemodel import Page

from django.db.models import (
    Model, Manager, CharField, URLField, IntegerField, ForeignKey
)

class Menu(Manager):
       
    def get_children(self, language, parent):
        return self.filter(language = language).filter(parent = parent).order_by('order')

    def get_root(self, language):
        return self.filter(url = "https://www.inkscape.org")



class MenuItem(Model):
    """A collection menus"""
    parent = ForeignKey('self', null=True, blank=True)
    url = URLField(help_text="Location of content.", unique=True)
    name = CharField(max_length=128)
    order = IntegerField(default=0)
    language = CharField(max_length=8, choices=settings.LANGUAGES)
    objects = Menu()
