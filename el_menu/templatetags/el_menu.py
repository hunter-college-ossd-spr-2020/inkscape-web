#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
#           2018, Jabiertxo Arraiza <jabiertxof@gmail.com>
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
Basic menu template tag
"""

from django.core.cache import cache
from django.conf import settings

from django.template import Library

from ..models import MenuItem

register = Library() # pylint: disable=invalid-name

def cache_key(lang):
    """Generate a caching key"""
    prefix = getattr(settings, 'MENU_CACHE_PREFIX', 'menu')
    return '%s_%s' % (prefix, lang)

def generate_menu(lang):
    """Generate the menu tree"""
    root_menu = []
    qset = MenuItem.objects.filter(root_id=lang)
    items = dict((item['pk'], {'item': item, 'submenu': []})
                 for item in qset.values('pk', 'parent', 'name', 'url'))
    items[None] = {'submenu': root_menu}

    for datum in items.values():
        if 'item' in datum:
            items[datum['item']['parent']]['submenu'].append(datum)

    return root_menu

@register.inclusion_tag('menu.html')
def render_menu(lang='en'):
    """Generates the menu as a list of dictionaries and submenu lists"""
    root_menu = cache.get(cache_key(lang), None)
    if not root_menu:
        root_menu = generate_menu(lang)
        cache.set(cache_key(lang), root_menu, getattr(settings, 'MENU_CACHE_DURATION', 300))
    return {'menu_items': root_menu}
