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

from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _

from haystack.views import search_view_factory
from cms.app_base import CMSApp

from cms.utils import i18n

from .utils import MonkeyCache
from .views import SearchView

class SearchApphook(CMSApp):
    name = _("search apphook")
    urls = [[
        url('^$', search_view_factory(SearchView), name='search'),
    ]]

i18n.get_languages = MonkeyCache(i18n.get_languages)
