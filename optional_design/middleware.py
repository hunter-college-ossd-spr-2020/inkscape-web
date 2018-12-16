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
Provide a middleware to identify when the request is an optional
design request and saves the right information.
"""

from . import set_design

class OptionalDesignMiddleware(object):
    """
    Control for optional designer flags.
    """
    @staticmethod
    def process_request(request):
        """Save the request in the loca thread for later use"""
        set_design(request.GET.get('od', None))

    @staticmethod
    def process_response(request, response):
        """Remove the request from the local thread on completion"""
        set_design(None)
        return response
