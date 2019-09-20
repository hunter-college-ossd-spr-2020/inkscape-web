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
# pylint: disable=too-few-public-methods,missing-docstring
"""
Election app mixins
"""

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.core.exceptions import PermissionDenied

class RestrictedMixin(object):
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if not self.is_allowed(request.user):
            raise PermissionDenied()
        return super(RestrictedMixin, self).dispatch(request, *args, **kwargs)

class TeamMemberMixin(RestrictedMixin):
    def is_allowed(self, user):
        """Test this user is a constituent of this election (voter)"""
        team = self.get_object().constituents
        return user.is_authenticated and team.has_member(user)

