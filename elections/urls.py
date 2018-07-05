# -*- coding: utf-8 -*-
#
# Copyright 2017, Martin Owens <doctormo@gmail.com>
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
"""Ways of interacting with the election app"""

from django.conf.urls import url
from inkscape.url_utils import url_tree

from .views import (
    ElectionList, ElectionDetail, ElectionAccept, ElectionInvite,
    ElectionInviteMessage, ElectionVote
)

urlpatterns = [ # pylint: disable=invalid-name
    url(r'^$', ElectionList.as_view(), name='list'),
    url_tree(
        r'^(?P<slug>[\w-]+)/',
        url(r'^$', ElectionDetail.as_view(), name='item'),
        url(r'^vote/(?P<hash>[\w-]+)/$', ElectionVote.as_view(), name='vote'),
        url_tree(
            r'^invite/',
            url_tree(
                r'^(?P<user_id>\d+)/',
                url('^$', ElectionInvite.as_view(), name='invite'),
                url('^msg/$', ElectionInviteMessage.as_view(), name='invite-msg'),
            ),
            url_tree(
                r'^(?P<hash>[\w-]+)/',
                url(r'^y/$', ElectionAccept.as_view(accepted=True), name='accept-yes'),
                url(r'^n/$', ElectionAccept.as_view(accepted=False), name='accept-no'),
            ),
        ),
    ),
]
