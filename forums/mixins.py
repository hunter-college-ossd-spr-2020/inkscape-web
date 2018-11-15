#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
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
# pylint: disable=no-member,too-few-public-methods
"""
Basic mixin classes for forums
"""

from django.db.models import Q
from django.utils import translation

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import Forum

class UserRequired(object):
    """Only allow a logged in user for flagging"""
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """Add login_required decorator to dispatch"""
        return super().dispatch(request, *args, **kwargs)

class ForumMixin(object):
    """Provide standard outputs for forum listings"""
    def get_forum_list(self):
        """Return a standard list of forums"""
        qset = Forum.objects.all()
        if not self.request.GET.get('all'):
            language = translation.get_language()
            qset = qset.filter(Q(lang=language) | Q(lang=''))
        return qset

    def get_context_data(self, **kwargs):
        """Add standard context data elements"""
        data = super().get_context_data(**kwargs)
        data['forums'] = self.get_forum_list()
        return data
