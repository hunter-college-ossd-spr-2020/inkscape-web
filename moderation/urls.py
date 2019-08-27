#
# Copyright 2014-2017, Martin Owens <doctormo@gmail.com>
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
"""Moderation views allow other parts of the website to be controlled by users"""

from django.conf.urls import url
from inkscape.url_utils import url_tree

from .views import (
    Moderation, ModerateType, UserFlag, CensureObject, UndecideObject,
    ApproveObject, NoteObject,
)

app_name = 'moderation'
urlpatterns = [ # pylint: disable=invalid-name
    url(r'^$', Moderation.as_view(), name="index"),
    url_tree(
        r'^(?P<app>[\w-]+)/(?P<name>[\w-]+)/',
        url(r'^$', ModerateType.as_view(), name="bytype"),

        url_tree(
            r'^(?P<pk>\d+)/',
            url(r'^$', UserFlag.as_view(), name='flag'),
            url(r'^censure/$', CensureObject.as_view(), name="censure"),
            url(r'^undecide/$', UndecideObject.as_view(), name="undecide"),
            url(r'^approve/$', ApproveObject.as_view(), name="approve"),
            url(r'^notes/$', NoteObject.as_view(), name="note"),
        )
    )
]
