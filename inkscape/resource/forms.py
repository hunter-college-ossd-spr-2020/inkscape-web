#
# Copyright 2013, Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Forms for the gallery system
"""
from django.forms import *
from django.utils.translation import ugettext_lazy as _

from .models import Resource, ResourceFile, Gallery

class GalleryForm(ModelForm):
    class Meta:
        model = Gallery
        fields = ['name']

class ResourceFileForm(ModelForm):
    permission = BooleanField(label=_('I have permission'), required=False)

    def __init__(self, *args, **kwargs):
        ModelForm.__init__(self, *args, **kwargs)
        for key in self.Meta.required:
            self.fields[key].required = True

    class Meta:
        model = ResourceFile
        fields = ['name', 'desc', 'link', 'category', 'license', 'published', 'owner', 'download']
        required = ['name', 'desc', 'category', 'license']

    def clean_owner(self):
        if self.cleaned_data.get('permission') != True and self.cleaned_data.get('owner') == False:
            raise ValidationError("You need to have permission to post this work, or be the owner of the work.")
        return self.cleaned_data.get('owner')

    def _clean_fields(self):
        super(ResourceFileForm, self)._clean_fields()
        if 'owner' in self._errors:
            self._errors['permission'] = self.errors['owner']

    @property
    def auto(self):
        for field in list(self):
            if field.name in ['name', 'desc', 'download']:
                continue
            yield field

class ResourceAddForm(ModelForm):
    class Meta:
        model = ResourceFile
        fields = ['download', 'name']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and name[0] == '$':
            self.cleaned_data['name'] = name[1:].rsplit('.',1)[0].replace('_',' ').replace('-',' ').title()[:64]
        return self.cleaned_data['name']

