# -*- coding: utf-8 -*-
#
# Copyright 2013-2018, Martin Owens <doctormo@gmail.com>
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
URLs that start with the *teamname pattern, and so are 'owned' by a specific team.
"""
from django.conf.urls import url, include
from inkscape.url_utils import url_tree

from .views import (
    TeamDetail, EditTeam, AddMember, RemoveMember, WatchTeam, UnwatchTeam,
    TeamCharter, ChatWithTeam, ChatLogs,
)

# '\*(?P<team>[^\/]+)/'
urlpatterns = [ # pylint: disable=invalid-name
    url(r'^$', TeamDetail.as_view(), name='team'),
    url(r'^edit/$', EditTeam.as_view(), name='team.edit'),
    url(r'^join/$', AddMember.as_view(), name='team.join'),
    url(r'^watch/$', WatchTeam.as_view(), name='team.watch'),
    url(r'^leave/$', RemoveMember.as_view(), name='team.leave'),
    url(r'^unwatch/$', UnwatchTeam.as_view(), name='team.unwatch'),
    url(r'^charter/$', TeamCharter.as_view(), name='team.charter'),
    url(r'^elections/', include('elections.urls', namespace='elections')),

    url(r'^chat/$', ChatWithTeam.as_view(), name='team.chat'),
    url(r'^chat/logs/$', ChatLogs.as_view(), name='team.chatlogs'),
    url_tree(
        r'^(?P<username>[^\/]+)/',
        url(r'^approve/$', AddMember.as_view(), name='team.approve'),
        url(r'^remove/$', RemoveMember.as_view(), name='team.remove'),
        url(r'^disapprove/$', RemoveMember.as_view(), name='team.disapprove'),
    ),
]
