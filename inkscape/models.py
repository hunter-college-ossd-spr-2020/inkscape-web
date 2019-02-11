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
Utility models which store data for the whole website's use.
"""
import urllib
import hashlib

from django.db.models import Model, CharField, FileField, URLField

from .utils import ReplaceStore, URLFile

class RemoteImage(Model):
    """
    When http images are included in parts of the website, this model will
    download the given url and store the file locally and return a url.
    """
    md5_prefix = CharField(max_length=16, null=True, blank=True)
    local_file = FileField(upload_to='remote', null=True, blank=True,
                           storage=ReplaceStore())
    remote_url = URLField()

    def get_absolute_url(self):
        """Return either the local or the remote url if available"""
        if self.local_file:
            return self.local_file.url
        return self.remote_url

    def save(self, **kw):
        """Download the remote url and store locally, replaces file if needed."""
        if not self.local_file:
            self.md5_prefix = hashlib.md5(self.remote_url.encode('utf8')).hexdigest()[:16]
            filename = str(self.remote_url).rsplit('/', 1)[-1]
            filename = (self.md5_prefix + '_' + filename)[-255:]
            try:
                self.local_file.save(filename, URLFile(self.remote_url), save=False)
            except urllib.error.HTTPError:
                # Set the local_file to an 'image not found'
                self.local_file.name = RemoteImage.objects.get(pk=1).local_file.name
        return super(RemoteImage, self).save(**kw)
