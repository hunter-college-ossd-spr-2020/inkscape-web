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

from django.utils import timezone
from datetime import timedelta

from django.db import utils
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView, ListView
from django.core.urlresolvers import reverse

from .models import *
from .mixins import *

class UserFlag(UserRequired, FlagView):
    title = _("Flag Object")
    confirm = _('Flagging Canceled')
    created = _('Moderators have been notified of the issue you have reported.')
    warning = _('You have already flagged this item for attention.')
    weight = FlagObject.USER_FLAG

    def function(self, flag, vote, created):
        if not created:
            return ('warning', 'warning')
        return ('success', 'created')


class Moderation(ModeratorRequired, ModerationMixin, ListView):
    title = _("Moderators' Area")
    display_days = 7

    def get_queryset(self):
        new = Q(resolution__isnull=True)
        recent = Q(updated__gt=now() - timedelta(days=self.display_days))
        return FlagObject.objects.filter(new | recent)
      
    def get_context_data(self, **kwargs):
        data = super(Moderation, self).get_context_data(**kwargs)
        data['user_flag_weight'] = FlagObject.USER_FLAG
        data['mod_approve_weight'] = FlagObject.MODERATOR_APPROVAL * -1
        data['mod_censure_weight'] = FlagObject.MODERATOR_CENSURE
        data['retain_threshold'] = FlagObject.RETAIN_THRESHOLD
        data['hiding_threshold'] = FlagObject.HIDING_THRESHOLD
        data['delete_threshold'] = FlagObject.DELETE_THRESHOLD
        data['display_days'] = self.display_days
        return data


class ModerateType(ModeratorRequired, ModerationMixin, ListView):
    template_name = 'moderation/flagobject_bytype.html'

    def get_queryset(self):
        new = Q(resolution__isnull=True)
        recent = Q(updated__gt=now() - timedelta(days=14))
        return FlagObject.objects.filter(new | recent)\
            .filter(content_type=self.contenttype)

    def get_context_data(self, **kwargs):
        data = super(ModerateType, self).get_context_data(**kwargs)
        data['model'] = list(data['object_list'].models)[0]
        data['title'] = _("Moderate Latest %s") % data['model']['label']
        data['parent'] = (reverse('moderation:index'), _('Moderation'))
        return data


class CensureObject(ModeratorRequired, FlagView):
    title = _("Censure Object")
    confirm = _('Censure Canceled')
    counted = _('Your vote to hide or delete has been counted.')
    hidden = _('Your vote resulted in the item being hidden.')
    deleted = _('Your vote resulted in the item being deleted.')
    weight = FlagObject.MODERATOR_CENSURE

    def function(self, flag, vote, created):
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
        elif flag.is_hidden:
            # is_removed only exists when is_hidden is true.
            flag.obj.is_removed = True
            flag.obj.ip_address = None
            flag.obj.save()
            return ('warning', 'hidden')

        return ('info', 'counted')

    def next_url(self):
        return reverse('moderation:index')

class UndecideObject(ModeratorRequired, FlagView):
    title = _("Undecided")
    confirm = _("Undecided vote Canceled")
    done = _('Your vote has been marked as undecided.')
    weight = FlagObject.MODERATOR_UNDECIDED

    def function(self, flag, vote, created):
        return ('success', 'done')

class ApproveObject(ModeratorRequired, FlagView):
    title = _("Approve Object")
    confirm = _('Approve Canceled')
    counted = _('Your vote to approve has been counted.')
    retained = _('Your vote resulted in the item being retained.')
    unhide = _('Your vote resulted in the item being unhidden.')
    weight = FlagObject.MODERATOR_APPROVAL

    def function(self, flag, vote, created):
        if flag.was_hidden:
            flag.obj.is_removed = False
            flag.obj.ip_address = None
            flag.obj.save()
            return ('success', 'unhide')
        if flag.is_retained:
            flag.resolution = True
            flag.save()
            return ('success', 'retained')
        return ('info', 'counted')

