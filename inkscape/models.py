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

from django.db.models import Model, CharField, IntegerField, DateTimeField,\
    FileField, TextField, URLField
from django.conf import settings

from .utils import ReplaceStore, URLFile

class ErrorLog(Model):
    uri    = CharField(max_length=255, db_index=True)
    status = IntegerField(db_index=True)
    count  = IntegerField(default=0)
    added  = DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ('-count',)

    def __str__(self):
        return "%s (%d)" % (self.uri, self.status)

    def add(self):
        self.count += 1
        self.save()

class HeartBeat(Model):
    """
    Track processes, updates and other items happening behind the scenes.
    """
    name = CharField(max_length=128, db_index=True, unique=True)
    status = IntegerField(default=0)
    error = TextField()

    beats = IntegerField(default=1)
    created = DateTimeField(auto_now_add=True)
    updated = DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, **kw):
        self.beats += 1
        super(HeartBeat, self).save(**kw)

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
            self.md5_prefix = hashlib.md5(self.remote_url).hexdigest()[:16]
            filename = str(self.remote_url).rsplit('/', 1)[-1]
            filename = (self.md5_prefix + '_' + filename)[-255:]
            try:
                self.local_file.save(filename, URLFile(self.remote_url), save=False)
            except urllib.error.HTTPError:
                # Set the local_file to an 'image not found'
                self.local_file.name = RemoteImage.objects.get(pk=1).local_file.name
        return super(RemoteImage, self).save(**kw)


# We could add this to middleware.py, but it's getting a bit full
# and this file is empty enough that it won't bother anyone.
class UserOnErrorMiddleware(object):
    """Add a link to the user in errors (if possible)"""
    cookie_key = getattr(settings, 'SESSION_COOKIE_NAME', None)

    def process_exception(self, request, exception):
        http = ['http', 'https'][request.META.get('HTTPS', 'off') == 'on']
        server = http + '://' + request.META.get('HTTP_HOST', 'localhost')

        # The database might have disapeared, so we can attempt
        # a link to the user, but otherwise the query contains the
        # session id, which is the pk for the admin.
        if self.cookie_key is not None:
            pk = request.COOKIES.get(self.cookie_key, None)
            if pk is not None:
                url = server + '/admin/user_sessions/session/%(pk)s/'
                request.META['SESSION_URL'] = url % {'pk': pk}
        # But try and put a direct link in anyway (if possible)
        try:
            if request.user.is_authenticated():
                url = request.user.get_absolute_url()
                request.META['USER_URL'] = server + url
        except:
            request.META['USER_URL'] = 'Error getting user'

