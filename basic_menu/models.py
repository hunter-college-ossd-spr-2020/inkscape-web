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
from django.utils.functional import cached_property
from cms.utils.conf import get_cms_setting
from django.contrib.sites.models import Site

from django.db.models import (
    Model, Manager, CharField, IntegerField, ForeignKey
)

class MenuRoot(Model):
    """A whole menu for a language"""
    language = CharField(max_length=12, choices=settings.LANGUAGES, primary_key=True)
    
#    @property
#    def cache_key(self):
#        prefix = get_cms_setting('CACHE_PREFIX')

#        key = '%sbasic_menu_nodes_%s_%s' % (prefix, self.language[0], Site.objects.get_current(request))

#        if self.request.user.is_authenticated():
#            key += '_%s_user' % self.request.user.pk

#        if self.draft_mode_active:
#            key += ':draft'
#        else:
#            key += ':public'
#        return key

#    @cached_property
#    def is_cached(self):
#        db_cache_key_lookup = CacheKey.objects.filter(
#            key=self.cache_key,
#            language=self.language[0],
#            site=self.site.pk,
#        )
#        return db_cache_key_lookup.exists()
#    
#    def show_menu(self):
#        key = self.cache_key

#        cached_nodes = cache.get(key, None)

#        if cached_nodes and self.is_cached:
#            # Only use the cache if the key is present in the database.
#            # This prevents a condition where keys which have been removed
#            # from the database due to a change in content, are still used.
#            return cached_nodes
#            
#        menuitems = MenuItem.objects.filter(root = self)
#        menu = []
#        for item in menuitems.filter(parent = None):
#            submenu = []
#            menudict = dict()
#            for subitem in menuitems.filter(parent = item):
#                submenudict = dict()
#                submenudict['url'] = subitem.url
#                submenudict['name'] = subitem.name
#                submenu.append(submenudict)
#            menudict['url'] = item.url
#            menudict['name'] = item.name
#            if len(submenu) > 0:
#                menudict['submenu'] = submenu
#            menu.append(menudict)
#        
#        cache.set(key, menu, get_cms_setting('CACHE_DURATIONS')['menus'])
#        
#        if not self.is_cached:
#            # No need to invalidate the internal lookup cache,
#            # just set the value directly.
#            self.__dict__['is_cached'] = True
#            # We need to have a list of the cache keys for languages and sites that
#            # span several processes - so we follow the Django way and share through
#            # the database. It's still cheaper than recomputing every time!
#            # This way we can selectively invalidate per-site and per-language,
#            # since the cache is shared but the keys aren't
#            CacheKey.objects.create(key=key, language=self.language[0], site=self.site.pk)
#        
#        return menu

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
    url = CharField(max_length=255, help_text="Location of content.")
    name = CharField(max_length=128)
    order = IntegerField(default=0)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return the linked content as this items url"""
        return self.url
