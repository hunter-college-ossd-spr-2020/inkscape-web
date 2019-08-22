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
Track the visiting people in the forum.
"""

from collections import OrderedDict
from datetime import timedelta

from django.conf import settings
from django.core.cache import caches
from django.utils.timezone import now

from person.models import User

# Age to count visits if users are really still here in minutes
VISITOR_AGE = timedelta(seconds=getattr(settings, 'FORUM_VISITOR_AGE', 20) * 60)

class RecentUsersMiddleware(object):
    """
    Record a list of users who have visited the forums recently.
    """
    cache = caches[settings.CACHE_MIDDLEWARE_ALIAS]

# django 2.0 code
#    def __init__(self, handler=None):
#        self.get_response = handler
#    def __call__(self, request):
#        return self.get_response(request)

    def set_visitor(self, user, at_time):
        """Record a user as visiting at this time"""
        visitors = self.get_visitors()
        visitors.pop(user.pk, None)
        visitors[user.pk] = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'last_seen': at_time,
        }
        if user.photo:
            visitors[user.pk]['photo_url'] = user.photo.url
        self.cache.set('visitors', list(visitors.items()))
        return visitors

    def get_visitors(self):
        """Return a sorteded list of visitors"""
        return OrderedDict((pk, visitor)
                           for pk, visitor in self.cache.get('visitors', [])[-20:]
                           if now() - visitor['last_seen'] < VISITOR_AGE)

    def process_template_response(self, request, response):
        """Add visiting user data into context"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            if getattr(settings, 'FORUM_DEBUG_ONLINE', False):
                # Add some test users when in debug mode
                user_qset = User.objects.exclude(photo__isnull=True).exclude(photo='')
                for user in user_qset.order_by('?')[:3]:
                    self.set_visitor(user, now())

            response.context_data['visitors'] = self.set_visitor(request.user, now())
        elif hasattr(response, 'context_data'):
            response.context_data['visitors'] = self.get_visitors()

        return response
