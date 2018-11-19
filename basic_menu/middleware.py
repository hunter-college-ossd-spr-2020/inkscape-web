#
# Copyright 2015, Martin Owens <doctormo@gmail.com>
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
Middleware for menu
"""
from django.conf import settings
from .models import MenuItem, Menu
from inkscape.utils import BaseMiddleware, to, context_items
# We could add this to middleware.py, but it's getting a bit full
# and this file is empty enough that it won't bother anyone.
class ShowMenu(BaseMiddleware):
    """
    This middleware controls and inserts menus
    into most pages. 
    """
    keys = ('menu')

    def process_template_response(self, request, response):
        if not hasattr(response, 'context_data'):
            return response
        data = response.context_data
        for key in self.keys:
            response.context_data[key] = self.get(data, key, then=self)
        return response

    def get_menu(self, data):
        """Return breadcrumbs only called if no breadcrumbs in context"""
        obj = self.get(data, 'object')
        data['menu'] = Menu().get_menu("es")

