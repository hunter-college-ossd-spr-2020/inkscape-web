#
# Copyright 2018, Jabiertxo Arraiza <jabiertxof@gmail.com>
#           2018, Martin Owens <doctormo@gmail.com>
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
Generates a menu for each available language using the django-cms
as a base. This should only be done once, then a manual process should take
over editing the links.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import AnonymousUser
from django.http.request import HttpRequest
from django.conf import settings

from menus.menu_pool import menu_pool, MenuRenderer

from ...models import MenuRoot, MenuItem

class Command(BaseCommand):
    """
    Calling this command should generate a menu per-language
    on the website.
    """
    def handle(self, **_): # pylint: disable=arguments-differ
        """Handle the generate menu command"""
        MenuItem.objects.all().delete()
        for lang, name in settings.LANGUAGES:
            print("Building menu for: {} ({})".format(name, lang))
            build_menu(lang)

def get_path(lang, path):
    """Generate the final path with language"""
    if lang == 'en' or not lang:
        return path
    return '/' + lang + path

def get_url(lang, node):
    """Return the right url for this cms node"""
    if node.attr and node.attr['redirect_url']:
        return node.attr['redirect_url']
    return get_path(lang, node.get_absolute_url())

def build_menu(lang):
    """
    Builds the given language's menu from django-cms
    """
    request = HttpRequest()
    request.user = AnonymousUser()
    request.path_info = "/" + lang + "/"

    cms_menu = MenuRenderer(menu_pool, request)

    (root, _) = MenuRoot.objects.get_or_create(language=lang)

    parents = {None: None}

    for x, node in enumerate(cms_menu.get_nodes()):
        if node.visible is True:
            if node.parent_id not in parents:
                print("Ignoring menu item {}".format(node.title))
                continue

            (parents[node.id], created) = \
                MenuItem.objects.update_or_create(cms_id=node.id, root=root, defaults={
                    'parent': parents[node.parent_id],
                    'name': node.title,
                    'url': get_url(lang, node),
                    'order': x,
                })

            if created:
                print(" + {}".format(node.title))
            else:
                print(" ~ {}".format(node.title))
