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
"""Releases allow inkscape to be downloaded."""

from django.conf.urls import url
from inkscape.url_utils import url_tree

from .views import DownloadRedirect, ReleaseView, PlatformList, ReleasePlatformView, PlatformView

version_urls = url_tree( # pylint: disable=invalid-name
    r'^(?P<version>[\w\+\.-]+)/',
    url('^$', ReleaseView.as_view(), name="release"),
    url(r'^platforms/$', PlatformList.as_view(), name="platforms"),

    # We don't use url_tree here because .+ competes with /dl/
    url('^(?P<platform>.+)/dl/$', ReleasePlatformView.as_view(), name="download"),
    url('^(?P<platform>.+)/$', PlatformView.as_view(), name="platform"),
)

urlpatterns = [ # pylint: disable=invalid-name
    url(r'^$', DownloadRedirect.as_view(), name="download"),
    url_tree(
        r'^(?P<project>[\w\-\.]+)-',
        version_urls,
    ),
    version_urls,
]
