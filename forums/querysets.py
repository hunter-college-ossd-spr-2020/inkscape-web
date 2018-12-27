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
Specialised querysets
"""
from collections import OrderedDict

from django.db.models import QuerySet, Model

class ForumQuerySet(QuerySet):
    """Query to help forums be grouped together"""
    def groups(self):
        """Batch each forum into groups by their name"""
        ret = OrderedDict()
        for item in self:
            if item.group.name not in ret:
                ret[item.group.name] = []
            ret[item.group.name].append(item)
        return ret

class TopicQuerySet(QuerySet):
    """
    Query the subscriptions in the same way that this topic is found.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.viewer = None
        self.subs = None
        self._subs_done = False

    def set_user(self, user):
        """Set the user looking at this this of topics"""
        self.viewer = user
        self.subs = None

    def _clone(self, **kwargs):
        clone = super()._clone(**kwargs)
        clone.viewer = self.viewer
        return clone

    def _subscriptions(self):
        # Late import becaue alert imports models
        from .alert import ForumTopicAlert
        return ForumTopicAlert.subscriptions_for(self.viewer)

    def subscriptions(self):
        """Return a list of subscriptions based on this queryset"""
        if self.subs is None:
            all_subs = self._subscriptions()
            self.subs = all_subs.filter(target__in=self.values_list('pk'))
        return self.subs

    def subscribed_only(self):
        """Filter the queryset to only include the subcriptions"""
        return self.filter(pk__in=self._subscriptions().values_list('target'))

    def _fetch_all(self):
        """Populate the subscriptions information as if it were a refetch_related"""
        super()._fetch_all()
        if not self._subs_done:
            subs = list(self.subscriptions().values_list('target', flat=True))
            for obj in self._result_cache:
                if isinstance(obj, Model):
                    obj.is_subscribed = obj.pk in subs
            self._subs_done = True

class UserFlagQuerySet(QuerySet):
    """
    Give access to special flags, such as banned users.
    """
    def banned(self):
        """Filter to only banned user_flags"""
        from .models import UserFlag
        return self.filter(flag=UserFlag.FLAG_BANNED)

    def moderators(self):
        """Filter to only moderator user_flags"""
        from .models import UserFlag
        return self.filter(flag=UserFlag.FLAG_MODERATOR)

    def custom_flags(self):
        """Filter to not mods or bans"""
        from .models import UserFlag
        return self.exclude(flag__in=[\
            UserFlag.FLAG_MODERATOR,
            UserFlag.FLAG_BANNED])
