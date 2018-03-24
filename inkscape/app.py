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

import logging
from django.apps import AppConfig
from django.conf import settings


class InkscapeConfig(AppConfig):
    name = 'inkscape'

    def ready(self):
        self.patch_cms()

    def patch_cms(self):
        """Patch away some aweful django-cms code"""
        from menus import utils

        class ReplacementLanguageChanger(utils.DefaultLanguageChanger):
            def __init__(self, request, controlled=False):
                if not controlled:
                    raise NotImplementedError("I refuse to give you a slow django-cms url!")
                super(ReplacementLanguageChanger, self).__init__(request)

        utils.DefaultLanguageChanger = ReplacementLanguageChanger

        from cms import cms_toolbars
        cms_toolbars.BasicToolbar.add_language_menu = lambda self: None

