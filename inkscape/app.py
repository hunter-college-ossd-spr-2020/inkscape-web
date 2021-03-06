#
# Copyright 2018, Martin Owens <doctormo@gmail.com>
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
Set up the inkscape app
"""
from django.apps import AppConfig

from django.conf import settings
from django.core.cache import caches
from django.views.generic.list import MultipleObjectMixin

from .pages import InkscapePaginator
from .utils import MonkeyCache, language_alternator

class InkscapeConfig(AppConfig):
    """The basic configuration for inkscape"""
    name = 'inkscape'
    cache = caches['default']

    def ready(self):
        self.patch_cms()
        self.add_language_fallbacks()
        MultipleObjectMixin.paginator_class = InkscapePaginator

    @staticmethod
    def add_language_fallbacks():
        """We have a better idea of languages than django-cms does."""
        langs = settings.CMS_LANGUAGES.setdefault(1, [])
        for lang, name in settings.LANGUAGES:
            langs.append({
                'name': name,
                'code': lang,
                'fallbacks': [alt for alt in language_alternator(lang)],
            })

    def patch_cms(self):
        """Patch away some aweful django-cms code"""
        from cms.models import Page as CmsPage
        from cms.utils.i18n import get_current_language

        slow_url = CmsPage.get_absolute_url
        def fast_url(self, language=None, fallback=True):
            """Replacement get_absolute_url functon"""
            if language is None:
                language = get_current_language()

            if not self.pk or not language:
                return slow_url(self, language=language, fallback=fallback)

            key = "{:d}:{:s}".format(self.pk, language)
            result = InkscapeConfig.cache.get(key)
            if not result:
                result = slow_url(self, language, fallback)
                InkscapeConfig.cache.set(key, result, 7 * 24 * 60 * 60)
            return result

        # We replace the url generator with a cached version (7 days!)
        CmsPage.get_absolute_url = fast_url

        # We don't like this toolbar, remove.
        from cms import cms_toolbars
        cms_toolbars.BasicToolbar.add_language_menu = lambda self: None

        # This language lookup is HIDEOUSLY slow
        from cms.utils import i18n
        i18n.get_languages = MonkeyCache(i18n.get_languages)
        i18n.get_redirect_on_fallback = lambda language, site_id=None: False 
        i18n.get_fallback_languages = MonkeyCache(i18n.get_fallback_languages, [0])
