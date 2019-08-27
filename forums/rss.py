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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with inkscape-web.If not, see <http://www.gnu.org/licenses/>.
#
# pylint: disable=attribute-defined-outside-init,protected-access
"""
All views required to show a list of forum topics.
"""

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.syndication.views import Feed

from .models import Forum, ForumTopic

class ForumTopicFeed(Feed):
    """Generate an RSS feed for forum topics."""
    def items(self, obj):
        """Returns the items for this feed, depends on query"""
        qset = ForumTopic.objects.all().select_related('forum')
        if isinstance(obj, Forum):
            qset = qset.filter(forum_id=obj.pk)
        elif obj:
            qset = qset.filter(first_username=obj)
        return qset.order_by('-last_posted')

    def get_object(self, request, slug=None, username=None):
        if slug:
            return Forum.objects.get(slug=slug)
        return username

    def link(self, obj):
        """Return the link to the list of items"""
        if isinstance(obj, Forum):
            return obj.get_absolute_url()
        elif obj:
            return reverse("forums:topic_list", kwargs={'username': obj})
        return reverse("forums:list")

    def description(self, obj):
        """Return the description of the feed"""
        if isinstance(obj, Forum):
            return obj.desc
        elif obj:
            return _("All topics posted by {}").format(obj)
        return _("All forum topics everwhere.")

    title = lambda self, obj: str(obj)
    item_link = lambda self, item: str(item.get_absolute_url())
    item_guid = lambda self, item: '#'+str(item.pk)
    item_title = lambda self, item: item.subject
    item_pubdate = lambda self, item: item.first_posted
    item_updateddate = lambda self, item: item.last_posted
    item_author_name = lambda self, item: str(item.first_username)

    link = ''
