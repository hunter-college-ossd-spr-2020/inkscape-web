#
# Copyright 2014-2017, Martin Owens <doctormo@gmail.com>
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
Provide some extra fields for django
"""

__all__ = ('AutoOneToOneField', 'ResizedImageField')

from django.db.models import OneToOneField
from django.db.models.fields.related import ReverseOneToOneDescriptor
from django.db.models.fields.files import ImageField, ImageFieldFile
from django.core.files.base import ContentFile

from PIL import Image, ExifTags
TAGS = dict(zip(ExifTags.TAGS.values(), ExifTags.TAGS.keys()))

CORRECTORE = {
    2: [Image.FLIP_LEFT_RIGHT],
    3: [Image.ROTATE_180],
    4: [Image.FLIP_TOP_BOTTOM],
    5: [Image.FLIP_LEFT_RIGHT, Image.ROTATE_90],
    6: [Image.ROTATE_270],
    7: [Image.FLIP_LEFT_RIGHT, Image.ROTATE_270],
    8: [Image.ROTATE_90],
}

from io import BytesIO

class AutoReverseOneToOneDescriptor(ReverseOneToOneDescriptor):
    def __get__(self, instance, instance_type=None):
        try:
            return super(AutoReverseOneToOneDescriptor, self).__get__(instance, instance_type)
        except self.related.model.DoesNotExist:
            obj = self.related.model(**{self.related.field.name: instance})
            obj.save()
            # Don't return obj directly, otherwise it won't be added
            # to Django's cache, and the first 2 calls to obj.relobj
            # will return 2 different in-memory objects
            return super(AutoReverseOneToOneDescriptor, self).__get__(instance, instance_type)


class AutoOneToOneField(OneToOneField):
    '''
    OneToOneField creates related object on first call if it doesnt exist yet.
    Use it instead of original OneToOne field.

    example:

        class MyProfile(models.Model):
            user = AutoOneToOneField(User, primary_key=True)
            home_page = models.URLField(max_length=255, blank=True)
            icq = models.IntegerField(max_length=255, null=True)
    '''
    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(), AutoReverseOneToOneDescriptor(related))


class ResizedImageFieldFile(ImageFieldFile):
    @staticmethod
    def _update_ext(filename, new_ext):
        parts = filename.split('.')
        parts[-1] = new_ext
        return '.'.join(parts)

    def save(self, name, content, save=True):
        content.file.seek(0)
        try:
            self.save_resized(name, Image.open(content.file), save=save)
        except OSError:
            pass

    def save_resized(self, name, img, save=True):
        """Resize the image using PIL"""
        new_content = BytesIO()

        if hasattr(img, '_getexif') and img._getexif():
            exif = dict(img._getexif().items())
            orientation = exif.get(TAGS.get('Orientation', None), None)
            for trans in CORRECTORE.get(orientation, []):
                img = img.transpose(trans)

        # In-place optional resize down to propotionate size
        img.thumbnail(self.field.maximum, Image.ANTIALIAS)

        if img.size[0] < self.field.minimum[0] or \
           img.size[1] < self.field.minimum[1]:
            ret = img.resize(self.field.minimum, Image.ANTIALIAS)
            img.im = ret.im
            img.mode = ret.mode
            img.size = self.field.minimum

        img.save(new_content, format=self.field.format)

        new_content = ContentFile(new_content.getvalue())
        new_name = self._update_ext(name, self.field.format.lower())
        super(ResizedImageFieldFile, self).save(new_name, new_content, save)



class ResizedImageField(ImageField):
    """
    Saves only a resized version of the image file. There are two possible transformations:

     - Image is too big, it will be proportionally resized to fit the bounds.
     - Image is too small, it will be resized with distortion to fit.

    """
    attr_class = ResizedImageFieldFile

    def deconstruct(self):
        name, path, args, kwargs = super(ResizedImageField, self).deconstruct()
        for arg in ('min_width', 'max_width',
                    'min_height', 'max_height', 'format'):
            kwargs[arg] = getattr(self, arg)
        return name, path, args, kwargs

    def __init__(self, verbose_name=None,
             max_width=100, max_height=100,
             min_width=0, min_height=0,
             format='PNG', *args, **kwargs):
        self.minimum = (min_width, min_height)
        self.maximum = (max_width, max_height)
        self.min_width = min_width
        self.max_width = max_width
        self.min_height = min_height
        self.max_height = max_height
        self.format = format
        super(ResizedImageField, self).__init__(verbose_name, *args, **kwargs)

