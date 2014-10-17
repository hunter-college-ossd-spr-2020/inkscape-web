#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
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

import os

from django.db.models import *

from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from django.core.urlresolvers import reverse

from pile.models import null

# Thread-safe current user middleware getter.
from cms.utils.permissions import get_current_user as get_user

class ProjectType(Model):
    value = CharField(_('Type Name'), max_length=128)

    def __str__(self):
        return self.value


class Project(Model):
    """A project details work that needs to be done"""
    sort   = IntegerField(_("Importance"))
    title  = CharField(_('Title'), max_length=100)
    slug   = SlugField(unique=True)

    banner   = ResizedImageFieldFile(_("Banner Logo"), max_height=120, max_width=650,
                          upload_to=os.path.join('project', 'banner'))
    logo     = ResizedImageFieldFile(_("Banner Logo"), max_height=150, max_width=150,
                          upload_to=os.path.join('project', 'logo'))

    duration = IntegerField(_('Expected Duration in Days'))
    started  = DateTimeField(**null)
    finished = DateTimeField(**null)

    created  = DateTimeField(auto_now_add=True, db_index=True)
    edited   = DateTimeField(auto_now=True)

    proposer = ForeignKey(User, related_name='proposed_projects', default=get_user)
    manager  = ForeignKey(User, related_name='manages_projects', **null)
    reviewer = ForeignKey(User, related_name='reviews_projects', **null)
    second   = ForeignKey(User, related_name='seconds_projects', **null)

    project_type = ForeignKey(ProjectType)

    is_fundable = BooleanField(default=False)
    is_approved = BooleanField(_('Pre-approved'), default=False)

    criteria = ManyToManyField('Criteria', **null)

    def __str__(self):
        return self.title

    def save(self, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        Model.save(self, **kwargs)

    def progress(self):
        """Returns a float, percentage of completed deliverable items"""
        count = self.deliverables.all().count()
        if count:
            done = self.deliverables.filter(complete=True).count()
            return (float(count) / done) * 100.0
        return self.finished and 100.0 or 0.0

    def get_absolute_url(self):
        return reverse('project', self.slug)


class Worker(Model):
    """Acts as both a statement of assignment and application process"""
    project  = ForeignKey(User, related_name='workers')
    user     = ForeignKey(User, related_name='works')

    plan     = TextField(**null)

    created  = DateTimeField(auto_now_add=True, db_index=True)
    vetted   = DateTimeField(**null)
    assigned = BooleanField(default=False)

    def __str__(self):
        p = (str(self.user), str(self.project))
        if not self.assigned:
            return "%s application for %s" % p
        return "%s working on %s" % p 


class Deliverable(Model):
    """A single deliverable item"""
    project  = ForeignKey(Project, related_name='deliverables')
    content  = CharField(_('Deliverable'), max_length=255)
    sort     = IntegerField(default=0)

    complete = BooleanField(default=False)
    
    def __str__(self):
        return self.content


class Criteria(Model):
    content  = CharField(_('Criteria'), max_length=255)
    detail   = TextField(**null)
    
    def __str__(self):
        return self.content


class ProjectUpdate(Model):
    """A project should always have at least one update with it's primary description"""

    describe = TextField(_("Description"))
    image    = ImageField(_("Image"), height_field=400, width_field=400,
                     upload_to=os.path.join('project', 'update', '%Y'), **null)

    creator  = ForeignKey(User, default=get_user)
    created  = DateTimeField(auto_now_add=True, db_index=True)
    edited   = DateTimeField(auto_now=True)

    def __str__(self):
        return self.describe



