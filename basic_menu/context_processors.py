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
from .views import MenuShow
from django.conf import settings
from django.core.cache import cache
from cms.utils import get_language_from_request

def basic_menu(request):
    context_data = dict()
    context_data['basic_menu'] = MenuShow(get_language_from_request(request), request).show_menu()
    path = request.get_full_path()
    if path[:16] == "/admin/cms/page/":
        lang = path.rsplit('=', 1)
        for language  in settings.LANGUAGES:
            if language[0] == lang[1]:
                menu_show = MenuShow(language, request)
                key = menu_show.cache_key
                cached_nodes = cache.get(key, None)
                if cached_nodes and self.is_cached:
                    cache.delete(key)
                menu_show.populize_lang()
                break
    return context_data


