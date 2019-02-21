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
Fields for forum forms
"""
from django.db.models.fields.files import FileField, FieldFile
from django.db.models import QuerySet
from django.contrib.staticfiles import storage
from django.forms import ValidationError, CharField
from resources.models import Resource

class ResourceList(CharField):
    """
    A list of resource primary keys (form field)
    """
    def prepare_value(self, value):
        if value is not None and value != '':
            if isinstance(value, QuerySet):
                return ",".join([str(pk) for pk in value.values_list('resource_id', flat=True)])
            return value
        return ''

    def to_python(self, value):
        """Convert csv of pks to resource items"""
        if value:
            try:
                pks = [int(pk) for pk in value.split(',')]
            except ValueError:
                raise ValidationError("Contains invalid primary key number.")
            return Resource.objects.filter(pk__in=pks)
        return []

class IconFile(FieldFile):
    """File attr class for IconField, does the dirty work."""
    @property
    def url(self):
        if self.field.fallback and not self:
            return storage.staticfiles_storage.url(self.field.fallback)
        return super().url

class IconField(FileField):
    """A file field (model field) with a default fallback static image."""
    attr_class = IconFile

    def __init__(self, *args, **kwargs):
        self.fallback = kwargs.pop('fallback', None)
        super().__init__(*args, **kwargs)
