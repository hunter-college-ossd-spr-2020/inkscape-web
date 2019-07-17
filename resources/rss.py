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
A resuable wrapper around django's syndication framework which
allows any ListView to be used as the basis for which items will
appear in an RSS feed.

This is DRY as it stops us repeating the complex work in resource
listing logic.
"""

import os

from django.conf import settings
from django.contrib.syndication.views import Feed, add_domain
from django.contrib.sites.shortcuts import get_current_site
from django.utils.feedgenerator import Rss201rev2Feed

class FeedGenerator(Rss201rev2Feed):
    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        if 'image_url' in self.feed and self.feed['image_url']:
            handler.startElement('image', {})
            handler.addQuickElement("url", self.feed['image_url'])
            handler.addQuickElement("title", self.feed['title'])
            handler.addQuickElement("link", self.feed['link'])
            handler.addQuickElement("width", self.feed['image_size'])
            handler.addQuickElement("height", self.feed['image_size'])
            handler.endElement(u'image')

class ListFeed(Feed):
    """
    Using the list_class view, generate an RSS for the user.
    """
    feed_type = FeedGenerator

    def feed_extra_kwargs(self, obj):
        """Add image tags"""
        return {
            'image_url': self._get_dynamic_attr('image_url', obj),
            'image_size': self._get_dynamic_attr('image_size', obj),
        }

    @property
    def list_class(self):
        """
        List class is another class based django view which will
        generate the list of items for this feed. It should typically
        be based on the ListView class but doesn't have to be.
        """
        raise NotImplementedError("list_class must be provided for RSS feeds")

    def __call__(self, request, *args, **kwargs):
        """Overload the __call__ to save the request data we need"""
        self.request = request
        self.args = args
        self.kwargs = kwargs
        return super().__call__(request, *args, **kwargs)

    @property
    def list(self):
        """Returns the category list for this feed (as a view)"""
        if not hasattr(self.request, '_list'):
            list_view = self.list_class.as_view()
            self.request._list = list_view(request=self.request, *self.args, **self.kwargs)
        return self.request._list


    def items(self):
        """Returns the items for this feed, depends on query"""
        context = self.list.context_data
        for item in context['object_list']:
            if item is not None:
                if 'query' in context:
                    if item.object is not None:
                        yield item.object
                else:
                    yield item

    item_link = lambda self, item: str(item().get_absolute_url())
    item_guid = lambda self, item: '#'+str(item().pk)
    item_title = lambda self, item: item().name
    item_pubdate = lambda self, item: item().created
    item_updateddate = lambda self, item: item().edited
    item_description = lambda self, item: item().description()
    item_author_name = lambda self, item: str(item().user)
    item_author_link = lambda self, item: item().user.get_absolute_url()

    item_enclosure_mime_type = lambda self, item: item().media_type
    item_enclosure_length = lambda self, item: item().download.size

    def item_enclosure_url(self, item):
        """Enclose the item (for viewing and playing)"""
        if item().download:
            return self.media_url(item().download.url)
        return None

    link = ''

    def media_url(self, url):
        """Gets the media URL for the resource"""
        if '://' not in url:
            url = os.path.join(settings.MEDIA_URL, url)
        if '://' not in url:
            # Localhost or same as site url
            current_site = get_current_site(self.request)
            url = add_domain(current_site.domain, url, self.request.is_secure())
        return url
