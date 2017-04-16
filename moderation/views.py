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

from django.utils import timezone
from datetime import timedelta

from django.db import utils
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, ListView
from django.core.urlresolvers import reverse

from .models import *
from .mixins import *

class UserFlag(UserRequired, FunctionView):
    title = _("Flag Object")
    confirm = _('Flagging Canceled')
    created = _('Moderators have been notified of the issue you have reported.')
    warning = _('You have already flagged this item for attention.')

    def function(self):
        (flag, created) = self.flag(weight=FlagObject.USER_FLAG)
        if not created:
            return ('warning', 'warning')
        return ('success', 'created')



class Moderation(ModeratorRequired, ListView):
    title = _("Moderators' Area")
    model = FlagObject

    def get_queryset(self):
        return FlagObject.objects.filter(
            Q(resolution__isnull=True) | Q(updated__gt=now() - timedelta(days=7))
        )


class ModerateLatest(ModeratorRequired, ListView):
    title = _("Moderate Latest Items")
    model = FlagObject


class CensureObject(ModeratorRequired, FunctionView):
    title = _("Censure Object")
    confirm = _('Censure Canceled')
    counted = _('Your vote to hide or delete has been counted.')
    hidden = _('Your vote resulted in the item being hidden.')
    deleted = _('Your vote resulted in the item being deleted.')

    def function(self, *args):
        (vote, created) = self.flag(weight=FlagObject.MODERATOR_CENSURE)
        flag = vote.target
        if flag.is_deleted:
            flag.resolution = False
            try:
                flag.save()
            except utils.IntegrityError:
                # Correct for when users are deleted but the object_owner
                # still points to the old user. Sometimes a transaction issue.
                flag.object_owner = None
                flag.save()

            return ('error', 'deleted')
        return ('info', 'counted')

    def next_url(self):
        return reverse('moderation:index')


class ApproveObject(ModeratorRequired, FunctionView):
    title = _("Approve Object")
    confirm = _('Approve Canceled')
    counted = _('Your vote to approve has been counted.')
    retained = _('Your vote resulted in the item being retained.')

    def function(self, *args):
        (flag, created) = self.flag(weight=FlagObject.MODERATOR_APPROVAL)
        flag = vote.target
        if flag.is_retained:
            flag.resolution = True
            flag.save()
            return ('success', 'retained')
        return ('info', 'counted')

