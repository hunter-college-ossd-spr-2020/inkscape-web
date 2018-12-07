#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
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
Forum views accessable from the website.
"""

from django.conf.urls import url
from inkscape.url_utils import url_tree

from .views import SelectSite, SelectForum, SelectThread, ImportThread

urlpatterns = [ # pylint: disable=invalid-name
    url(r'^$', SelectSite.as_view(), name="select_site"),
    url_tree(
        r'^(?P<site>[^\/]+)/',
        url(r'^$', SelectForum.as_view(), name="select_forum"),
        url_tree(
            r'^(?P<forum>[^\/]+)/',
            url(r'^$', SelectThread.as_view(), name="select_thread"),
            url(r'^(?P<thread>[^\/])/$', ImportThread.as_view(), name="import_thread"),
        ),
    ),
]
