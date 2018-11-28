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
# pylint: disable=too-many-ancestors
"""
Basic view extensions
"""

from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.base import View

FLIP_VALUE = "!"
INCREMENT = "+1"
DECREMENT = "-1"

class FieldUpdateView(SingleObjectMixin, View):
    """
    Take an object and change the value on one of the fields
    during the get request.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = {}

    def get_field(self):
        """Generate the field name that is being updated"""
        return self.field

    def get_value(self, start, field):
        """Calculate the value based on some basic examples"""
        value = self.value
        if value == FLIP_VALUE:
            return not start
        elif value == INCREMENT:
            return start + 1
        elif value == DECREMENT:
            return start - 1
        return value

    def get(self, request, *args, **kwargs):
        """We don't use POST for fieldging"""
        obj = self.get_object()
        field = self.get_field()
        start = getattr(obj, field, None)
        value = self.get_value(start, field)

        self._saved = {field: value}
        if start != value:
            setattr(obj, field, value)
            obj.save(update_fields=[field])
            data = self.field_changed(obj, **self._saved)
        else:
            data = self.field_unchanged(obj, **self._saved)

        if 'next' in request.GET:
            return HttpResponseRedirect(request.GET['next'])
        return JsonResponse(data)

    def log_details(self):
        """A brief log returned via json if no next sepcified"""
        return self._saved

    @property
    def field(self):
        """The name of the field to update"""
        raise NotImplementedError("Please provide a field name to change.")

    @property
    def value(self):
        """The value to change this value to"""
        return self.request.GET.get('value')

    def field_changed(self, obj, **data):
        """Called after a successful save of the data"""
        if obj is not None and self is not None:
            return data
        return None

    def field_unchanged(self, obj, **data):
        """Called when the data hasn't changed, nothing saved"""
        if obj is not None and self is not None:
            return data
        return None
