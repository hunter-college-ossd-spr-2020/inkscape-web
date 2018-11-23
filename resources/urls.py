# -*- coding: utf-8 -*-
#
# Copyright 2013, Martin Owens <doctormo@gmail.com>
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
"""Resources provide galleries, downloads and other important parts"""

from django.conf.urls import url
from inkscape.url_utils import url_tree
from person import user_urls, team_urls

from .views import (
    ResourceList, ResourcePick, ResourceFeed, ResourceJson, ViewResource,
    GalleryList, GalleryView, GalleryFeed, CreateGallery,
    PasteInResource, UploadResource, DropResource, LinkToResource,
    DeleteGallery, EditGallery, DeleteResource, EditResource, PublishResource,
    MoveResource, DownloadReadme, VoteResource, DownloadResource,
    TagsJson, QuotaJson, ResourcesJson,
)

def resource_search(*args, lst=ResourceList, feed=ResourceFeed,
                    pick=ResourcePick, json=ResourceJson):
    """Generate standard url patterns for resource listing"""
    return [
        url(r'^$', lst.as_view(), name='resources'),
        url(r'^rss/$', feed(), name='resources_rss'),
        url(r'^pick/$', pick.as_view(), name='resources_pick'),
        url(r'^json/$', json.as_view(), name='resources_json'),
        url_tree(
            r'^=(?P<category>[^\/]+)/',
            url(r'^$', lst.as_view(), name='resources'),
            url(r'^rss/$', feed(), name='resources_rss'),
            url(r'^json/$', json.as_view(), name='resources_json'),
            *args)
    ]

owner_patterns = [ # pylint: disable=invalid-name
    url_tree(
        r'^galleries/',
        url(r'^$', GalleryList.as_view(), name='galleries'),
        url_tree(r'^(?P<galleries>[^\/]+)/', *resource_search(lst=GalleryView, feed=GalleryFeed)),
    ),
    url_tree(r'^resources/', *resource_search()),
]
user_patterns = [ # pylint: disable=invalid-name
    # Try a utf-8 url, see if it breaks web browsers.
    url(r'^★(?P<slug>[^\/]+)$', ViewResource.as_view(), name='resource'),
]
# Add to the username user profile and teamname
user_urls.urlpatterns += list(owner_patterns + user_patterns)
team_urls.urlpatterns += list(owner_patterns)

urlpatterns = [ # pylint: disable=invalid-name
    url(r'^paste/(?P<pk>\d+)/$', ViewResource.as_view(), name='pasted_item'),
    url(r'^json/tags.json$', TagsJson.as_view(), name='tags.json'),
    url(r'^json/quota.json$', QuotaJson.as_view(), name='quota.json'),
    url(r'^json/resources.json$', ResourcesJson.as_view(), name='resources.json'),

    url_tree(
        r'^gallery/',
        url(r'^new/$', CreateGallery.as_view(), name='new_gallery'),
        url(r'^link/$', LinkToResource.as_view(), name='resource.link'),
        url(r'^paste/$', PasteInResource.as_view(), name='pastebin'),
        url(r'^upload/$', UploadResource.as_view(), name='resource.upload'),
        url(r'^upload/go/$', DropResource.as_view(), name='resource.drop'),

        url_tree(
            r'^(?P<gallery_id>\d+)/',
            # We should move these to galleries/
            url(r'^del/$', DeleteGallery.as_view(), name='gallery.delete'),
            url(r'^link/$', LinkToResource.as_view(), name='resource.link'),
            url(r'^edit/$', EditGallery.as_view(), name='gallery.edit'),
            url(r'^upload/$', UploadResource.as_view(), name='resource.upload'),
            url(r'^upload/go/$', DropResource.as_view(), name='resource.drop'),
        ),

        url_tree(
            r'^item/(?P<pk>\d+)/',
            url(r'^$', ViewResource.as_view(), name='resource'),
            url(r'^del/$', DeleteResource.as_view(), name='delete_resource'),
            url(r'^pub/$', PublishResource.as_view(), name='publish_resource'),
            url(r'^edit/$', EditResource.as_view(), name='edit_resource'),
            url(r'^view/$', DownloadResource.as_view(), name='view_resource'),
            url(r'^move/(?P<source>\d+)/$', MoveResource.as_view(), name='resource.move'),
            url(r'^copy/$', MoveResource.as_view(), name='resource.copy'),
            url(r'^readme.txt$', DownloadReadme.as_view(), name='resource.readme'),
            url(r'^(?P<like>[\+\-])$', VoteResource.as_view(), name='resource.like'),
            url(r'^(?P<fn>[^\/]+)/?$', DownloadResource.as_view(), name='download_resource'),
        ),
        *resource_search(
            url(r'^(?P<galleries>[^\/]+)/', GalleryView.as_view(), name='resources'),
            url(r'^(?P<galleries>[^\/]+)/rss/', GalleryFeed(), name='resources_rss'),
            url(r'^(?P<galleries>[^\/]+)/json/', ResourceJson.as_view(), name='resources_json'),
        )
    ),
]
