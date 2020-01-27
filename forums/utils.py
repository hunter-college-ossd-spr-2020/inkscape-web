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
# pylint: disable=too-many-ancestors
#
"""
Forum utils.
"""

import re
from unidecode import unidecode
from bs4 import BeautifulSoup
from django.templatetags.static import static

from resources.models import Resource

def clean_comment(comment):
    """Clean the comment of unwanted elements"""
    embedded_pks = comment.attachments.embedded_pks()
    soup = BeautifulSoup(comment.comment, 'html5lib')
    # Remove some bad tags we don't want
    for tag in soup(['iframe', 'script', 'object', 'embed']):
        tag.extract()
    # Check html for image tags.
    external_image = static('forums/images/external_image.png')
    broken_image = static('forums/images/broken_image.png')
    for tag in soup(['img']):
        tag_id = tag.get('id', '')
        if tag_id.startswith('inline_'):
            try:
                pkey = int(tag_id.split('_', 1)[1])
                resource = Resource.objects.get(pk=pkey)
                if resource.mime().is_image():
                    tag['src'] = resource.download.url
                else:
                    tag['src'] = resource.thumbnail_url()
            except (ValueError, Resource.DoesNotExist):
                tag['src'] = broken_image
        else:
            tag['src'] = external_image
    # Remove script and other tags
    return str(soup)

def ascii_whitewash(text):
    """
    Remove unicode, symbols and multple spaces to give the cleanest
    version of any string.
    """
    # Convert unicode into nearest ascii/romanised equiv
    text = unidecode(text)
    # Remove any remaining symbols and replace with spaces
    text = re.sub(r'[^0-9a-zA-Z]', ' ', text)
    # Replace all multiple spaces with one space
    return re.sub(r'\s+', ' ', text).lower()
