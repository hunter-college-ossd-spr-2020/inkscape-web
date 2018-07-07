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
URLs that start with the ~username pattern, and so are 'owned' by a specific user.
"""

from django.conf.urls import url

from alerts.views import CreateMessage
from .views import (
    UserDetail, UserGPGKey, MakeFriend, LeaveFriend,
)

# r'^~(?P<username>[^\/]+)/',
urlpatterns = [ # pylint: disable=invalid-name
    url(r'^$', UserDetail.as_view(), name='view_profile'),
    url(r'^gpg/$', UserGPGKey.as_view(), name='user_gpgkey'),
    url(r'^friend/$', MakeFriend.as_view(), name='user_friend'),
    url(r'^unfriend/$', LeaveFriend.as_view(), name='user_unfriend'),
    # Example message system
    url(r'^message/$', CreateMessage.as_view(), name="message.new"),
    url(r'^message/(?P<pk>\d+)/$', CreateMessage.as_view(), name="message.reply"),
]
