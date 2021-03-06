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

from ..models import MenuItem, MenuTranslation

register = Library() # pylint: disable=invalid-name

DURATION = getattr(settings, 'MENU_CACHE_DURATION', 300)

def cache_key(lang, category='menu'):
    """Generate a caching key"""
    key = category.upper() + '_CACHE_PREFIX'
    prefix = getattr(settings, key, category)
    return '%s_%s' % (prefix, lang)

def generate_menu(lang, category=None):
    """Generate the menu tree"""
    if category == 'menu':
        category = None
    root_menu = []
    lang_qset = MenuItem.objects.filter(lang__in=(lang, 'all'))\
        .filter(category=category)\
        .order_by('order')
    all_qset = MenuTranslation.objects.filter(language=lang)\
        .select_related('item')\
        .filter(item__category=category)\
        .order_by('item__order')

    items = dict((item['pk'], {'item': item, 'submenu': []})
                 for item in lang_qset.values('pk', 'parent', 'name', 'url', 'title'))
    items.update((item['item__pk'], {'item': {
        'pk': item['item__pk'],
        'parent': item['item__parent'],
        'name': item['name'] or item['item__name'],
        'url': item['url'] or item['item__url'],
        'title': item['title'] or item['item__title'],
    }, 'submenu': []}) for item in all_qset.values(
        'item__pk', 'item__parent', 'item__name', 'item__url', 'item__title',
        'name', 'url', 'title'))

    items[None] = {'submenu': root_menu}

    for datum in items.values():
        # This will stop any
        if 'item' in datum and datum['item']['parent'] in items:
            items[datum['item']['parent']]['submenu'].append(datum)

    return root_menu

def render_or_cache(lang, category):
    """Generates any menu"""
    ckey = cache_key(lang, category)
    root_foot = cache.get(ckey, None)
    if root_foot is None:
        root_foot = generate_menu(lang, category)
        cache.set(ckey, root_foot, DURATION)
    return {'menu_items': root_foot}

def clear_cache(lang, category):
    """Clears the category"""
    if category is None:
        category = 'menu'
    ckey = cache_key(lang, category)
    return cache.delete(ckey)

@register.inclusion_tag('menu.html')
def render_menu(lang='en'):
    """Generates the menu as a list of dictionaries and submenu lists"""
    return render_or_cache(lang, 'menu')

@register.inclusion_tag('foot.html')
def render_foot(lang='en'):
    """Generates the footer as a list of dictionaries and submenu lists"""
    return render_or_cache(lang, 'foot')

@register.inclusion_tag('tabs.html')
def render_tabs(lang='en'):
    """Generates the extra tabs as a list of dictionaries and submenu lists"""
    return render_or_cache(lang, 'tab')
