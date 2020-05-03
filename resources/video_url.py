#
# Copyright 2014-2019, Martin Owens <doctormo@gmail.com>
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
Scan for Video URLs and gather together meta data about them.
"""

import re
import json

from urllib.request import urlopen
from urllib.parse import parse_qs

from .utils import url_filefield

VIDEO_URLS = {
    'youtube': r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be'
               r'/)(watch\?v=|embed/|v/|.+\?v=)?(?P<video_id>[^&=%\?]{11})',
    'vimeo': r'(http:\/\/)?(www\.)?(vimeo\.com)(\/channels\/.+)?\/(?P<video_id>.+)/?',
}

def noop_data(video):
    """Do nothing"""
    return video

def youtube_data(video, debug=False):
    """
    Gather more data about this video from youtube.

    Will modify video dictionary 'in-place'
    """
    uri = "https://youtube.com/get_video_info?video_id={id}".format(**video)
    try:
        response = urlopen(uri)
        data = parse_qs(response.read().decode())
        if 'player_response' in data:
            data = json.loads(data['player_response'][0])['videoDetails']
            data['thumbnail_url'] = data['thumbnail']['thumbnails'][-1]['url']
            data['description'] = data['shortDescription']
        if debug:
            return data

        for field in ('title', 'author', 'thumbnail_url',
                      'description', 'lengthSeconds', 'keywords'):
            if field in data:
                video[field] = data[field]
    except Exception: # pylint: disable=broad-except
        pass
    return video

def video_detect(url, metadata=False):
    """
    Embed the video using known video_urls.

    If metadata is True, it will attempt to gather more information about the video (such as title)
    but this may take longer as it must make external requests.
    """
    if url is not None:
        for site_id, regex in VIDEO_URLS.items():
            match = re.match(regex, url)
            if not match:
                continue
            vid = match.group('video_id')
            ret = {
                'type': site_id, 'id': vid,
                'title': f"Video Link {vid}",
                'author': "Unknown Author",
                'description': "-",
                'thumbnail_url': None,
                'lengthSeconds': None,
                'keywords': [],
            }
            if metadata:
                globals().get(site_id + '_data', noop_data)(ret)
            return ret
    return None


def parse_any_url(query, user):
    """
    We want to parse a given URL and decide if it's a video URL
    or some other interesting or important URL.

    Returns the Resource object matched / used or None if not found.
    """
    from .models import Resource, Tag
    is_video = video_detect(query)
    if is_video:
        # Find an existing video in our resource database that matches.
        for match in Resource.objects.filter(link__contains=is_video['id']):
            match_v = match.video
            if match_v \
                  and match_v['id'] == is_video['id'] \
                  and match_v['type'] == is_video['type']:
                return match

        if user.is_authenticated():
            # Create a new video object in our resource database.
            details = video_detect(query, True)
            obj = Resource(
                user=user,
                name=details['title'],
                desc=details['description'],
                owner_name=details['author'],
                media_x=details['lengthSeconds'],
                rendering=url_filefield(details['thumbnail_url'],
                                        'video_' + details['id'] + '.png'),
                link=query, owner=False, published=False)
            obj.save()
            for tag in details['keywords']:
                if len(tag) < 16:
                    obj.tags.add(Tag.objects.get_or_create(name=tag.lower())[0])
            return obj

    if query.rsplit('.', 1)[-1] in ('png', 'svg', 'jpeg', 'jpg'):
        # Linked image on another website
        filename = query.split('?')[0].split('/')[-1]

        for match in Resource.objects.filter(link=query):
            return str(match.pk)

        if user.is_authenticated():
            # Create a new image link object in our resource database.
            ret = Resource(
                user=user,
                name='Linked Image (' + filename + ')',
                owner_name='Internet',
                rendering=url_filefield(query, filename),
                link=query, owner=False, published=False)
            ret.save()
            return ret
    return None
