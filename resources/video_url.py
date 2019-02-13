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

from urllib.request import urlopen
from urllib.parse import parse_qs

VIDEO_URLS = {
    'youtube': r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be'
               r'/)(watch\?v=|embed/|v/|.+\?v=)?(?P<video_id>[^&=%\?]{11})',
    'vimeo': r'(http:\/\/)?(www\.)?(vimeo\.com)(\/channels\/.+)?\/(?P<video_id>.+)/?',
}

def noop_data(video):
    """Do nothing"""
    return video

def youtube_data(video):
    """
    Gather more data about this video from youtube.

    Will modify video dictionary 'in-place'
    """
    uri = "https://youtube.com/get_video_info?video_id={id}".format(**video)
    try:
        response = urlopen(uri)
        data = parse_qs(response.read().decode())
        for field in ('title', 'author', 'thumbnail_url'):
            if field in data:
                video[field] = data[field][0]
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
            ret = {'type': site_id, 'id': match.group('video_id')}
            if metadata:
                globals().get(site_id + '_data', noop_data)(ret)
                if 'title' not in ret:
                    ret['title'] = "Video Link {id}".format(**ret)
                if 'author' not in ret:
                    ret['author'] = "Unknown Author"
                if 'thumbnail_url' not in ret:
                    ret['thumbnail_url'] = None
            return ret
    return None
