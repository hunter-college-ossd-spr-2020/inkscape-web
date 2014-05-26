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
Models for resource system, provides license, categories and resource downloads.
"""

import os

from django.db.models import *
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Group
from django.utils.timezone import now

from inkscape.fields import ResizedImageField

null = dict(null=True, blank=True)
def upto(d, c='resources', blank=True, lots=False):
    dated = lots and ["%Y","%m"] or []
    return dict(null=blank, blank=blank, upload_to=os.path.join(c, d, *dated))

class License(Model):
    name    = CharField(max_length=64)
    code    = CharField(max_length=16)
    link    = URLField(**null)
    banner  = FileField(_('License Banner (svg:80x15)'), **upto('banner', 'license'))
    icon    = FileField(_('License Icon (svg:100x40)'), **upto('icon', 'license'))

    at  = BooleanField(_('Attribution'), default=True)
    sa  = BooleanField(_('Copyleft (Share Alike)'), default=False)
    nc  = BooleanField(_('Non-Commercial'), default=False)
    nd  = BooleanField(_('Non-Derivitive'), default=False)

    replaced = ForeignKey("License", verbose_name=_('Replaced by'), **null)

    def is_free(self):
        return not self.nc and not self.nd and not arr

    def is_all_rights(self):
        return self.nc and self.nd and not self.at

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.code)


class Category(Model):
    name     = CharField(max_length=64)
    desc     = TextField(**null)

    acceptable_licenses = ManyToManyField(License)

    def __unicode__(self):
        return self.name


class Resource(Model):
    user      = ForeignKey(User, related_name='resources')
    name      = CharField(max_length=64)
    desc      = TextField(_('Description'), **null)
    category  = ForeignKey(Category, related_name='items', **null)

    created   = DateTimeField(default=now)
    edited    = DateTimeField(**null)
    published = BooleanField(default=True)

    thumbnail = ResizedImageField(_('Thumbnail'), 190, 190, **upto('thumb'))

    link      = URLField(_('More Info URL'), **null)

    def __unicode__(self):
        return self.name

    def is_visible(self, user_id):
        return user_id == self.user.id or self.published

    def save(self, *args, **kwargs):
        self.edited = now()
        return Model.save(self, *args, **kwargs)

    @property
    def outer(self):
        if type(self) is Resource:
            if hasattr(self, 'resourcefile'):
                return self.resourcefile
            elif hasattr(self, 'resourceurl'):
                return self.resourceurl
        return self

    def download(self):
        return self.outer.download_url()

    def download_url(self):
        return self.link


class ResourceFile(Resource):
    """This is a resource with an uploaded file"""
    download = FileField(_('Consumable File'), **upto('file', blank=False))

    license   = ForeignKey(License, **null)
    owner     = BooleanField(_('I own this work'), default=True)

    def download_url(self):
        return self.download.url

    def is_file(self):
        return True

    def is_image(self):
        """Returns true if the download is an image (svg/png/jpeg/gif)"""
        return download_url.rsplit('.', 1)[-1] in ['svg','png','jpeg','jpg']


class Gallery(Model):
    user      = ForeignKey(User, related_name='galleries')
    name      = CharField(max_length=64)
    items     = ManyToManyField(Resource)

    def __unicode__(self):
        return self.name


class ResourceUrl(Resource):
    """This is a resource that links to somewhere else"""
    download = URLField(_('Consumable File'), **null)
    source   = URLField(_('Source File'), **null)

    def download_url(self):
        return self.download

    def source_url(self):
        return self.source

    def is_link(self):
        return True


VOTES = ['Likes', 'Dislikes', 'Verified', 'Promotes']
VOTE_CHOICE = [(i, VOTES[i]) for i in range(len(VOTES))]

class Vote(Model):
    """Vote for a resource in some way"""
    resource = ForeignKey(Resource, related_name='votes')
    voter    = ForeignKey(User, related_name='votes')
    vote     = IntegerField(_('Vote'), default=0, choices=VOTE_CHOICE)
    
    def __str__(self):
        return "%s %s %s " % (str(self.voter), self.votetype, str(self.resource))

    @property
    def votetype(self):
        return VOTES[self.vote]


