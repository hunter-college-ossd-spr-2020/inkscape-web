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
"""
Load inkscape docs from the disk and give to the user.
"""
import re
import os
import codecs

from django.utils.translation import get_language_from_path, get_language_from_request

from django.http import Http404
from django.shortcuts import render

from django.conf import settings

DOC_ROOT = os.path.join(settings.MEDIA_ROOT, 'doc')

def get_redirects():
    """We want to open up a redirects files with all the right
       Instructions, but this mustn't break the site if they fail."""
    if os.path.isdir(DOC_ROOT):
        _file = os.path.join(DOC_ROOT, 'redirects.re')
        if os.path.isfile(_file):
            with open(_file, 'r') as fhl:
                return [ line.strip().split("|") for line in fhl.readlines() ]
    return []

def get_path(uri):
    path = os.path.join(DOC_ROOT, uri)
    if os.path.isfile(path):
        return (path, uri)

    for (regex, new_uri) in get_redirects():
        try:
            ret = re.findall(regex, uri)
            assert ret
            uri = new_uri % ret[0]
            path = os.path.join(DOC_ROOT, uri)
            if os.path.isfile(path):
                return (path, uri)
        except (AssertionError):
            # We capture all exceptions to protect from broken regexs
            pass
    
    raise Http404

def get_localized_path(path, language):
    # normalize some language names that differ between inkscape-web and docs
    if language == 'pt-br':
        language = 'pt_BR'
    if language == 'zh':
        language = 'zh_CN'
    if language == 'zh-hant':
        language = 'zh_TW'

    localized_path = path[:-4] + language + '.html'
    if os.path.isfile(localized_path):
        return localized_path

    return path

def page(request, url, lang=None):
    """
    Try and find the document page.
    """
    (path, uri) = get_path(url)
    if os.path.isdir(path) or path[-5:] != '.html':
        raise Http404

    if not lang:
        lang = get_language_from_path(request.path)
        if lang in (None, ''):
            lang = 'en'

    path = get_localized_path(path, lang)

    with codecs.open(path, "r", "utf-8") as fhl:
        content = fhl.read()
        # extract metadata from <head>
        title = content.split('<title>',1)[-1].split('</title>',1)[0]
        # extract <body> as content (and rewrite to <div>)
        content = content.split('<body',1)[-1].split('</body',1)[0]
        content = '<div' + content + '</div>'
        # replace relative links with absolute links prefixed with MEDIA_URL
        content = content.replace('src="http','|src|')\
            .replace('src="', 'src="%s/' % os.path.join(settings.MEDIA_URL,
              'doc', *uri.split('/')[:-1]))\
            .replace('|src|', 'src="http')
    context = {
        'path': path,
        'lang': lang,
        'title': title,
        'content': content,
    }
    return render(request, 'docs/page.html', context)
