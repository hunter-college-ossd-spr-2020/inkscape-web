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
"""
Middleware for cog errors
"""
from django.conf import settings

# We could add this to middleware.py, but it's getting a bit full
# and this file is empty enough that it won't bother anyone.
class UserOnErrorMiddleware(object):
    """Add a link to the user in errors (if possible)"""
    cookie_key = getattr(settings, 'SESSION_COOKIE_NAME', None)

    def __init__(self):
        self.server = None

    def process_exception(self, request, exception):
        """When each request is made, this is run to add users"""
        http = 'https' if request.META.get('HTTPS', 'off') == 'on' else 'http'
        self.server = http + '://' + request.META.get('HTTP_HOST', 'localhost')

        # The database might have disapeared, so we can attempt
        # a link to the user, but otherwise the query contains the
        # session id, which is the pk for the admin.
        if self.cookie_key is not None:
            pkey = request.COOKIES.get(self.cookie_key, None)
            if pkey is not None:
                url = self.server + '/admin/user_sessions/session/%(pk)s/'
                request.META['SESSION_URL'] = url % {'pk': pkey}
        self.direct_link(request)

    def direct_link(self, request):
        """But try and put a direct link in anyway (if possible)"""
        try:
            if request.user.is_authenticated():
                url = request.user.get_absolute_url()
                request.META['USER_URL'] = self.server + url
        except KeyError:
            request.META['USER_URL'] = 'Error getting user'
