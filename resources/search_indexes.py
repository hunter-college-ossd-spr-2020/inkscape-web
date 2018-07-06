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
"""Define how resources can be searched"""

from haystack.indexes import SearchIndex, Indexable, \
    DateTimeField, BooleanField, CharField

from .models import Resource
from .views import ResourceList
from .search_base import add_fields

class ResourceIndex(SearchIndex, Indexable):
    """Main index for each resource"""
    text = CharField(document=True, use_template=True)
    edited = DateTimeField(model_attr='edited', null=True)
    created = DateTimeField(model_attr='created', null=True)
    published = BooleanField(model_attr='published')

    def get_model(self):
        return Resource

    def get_updated_field(self):
        return 'edited'

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        # This would need changing if we used the signal updater
        return self.get_model().objects.filter(published=True, is_removed=False)


# This adds the extra indexable fields that the category list uses.
add_fields(ResourceIndex, ResourceList)
