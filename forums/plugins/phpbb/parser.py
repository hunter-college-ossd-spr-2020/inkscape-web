# -*- coding: utf-8 -*-
#
# Copyright 2014-2018, Martin Owens <doctormo@gmail.com>
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
Manage the download or syncing of a phpbb forum.
"""

import os
import re
import stat
import time
import json
import types
import hashlib
import logging

from collections import OrderedDict
from urllib.request import urlopen, Request
from urllib.parse import urlparse, parse_qs, urljoin

from django.conf import settings

try:
    from bs4 import BeautifulSoup
except ImportError:
    bs4 = None
    logging.error("Python module 'BeautifulSoup' required to do phpBB syncing.")

EMOJI = {
    ':)': '😊',
    ':-)': '☺️',
    ';)': '😉',
    ';-)': '😉', # ./images/smilies/icon_e_wink.gif
    ':D': '😀',
    ':-D': '😀', # ./images/smilies/icon_e_biggrin.gif
    ':(': '☹',
    ':-(': '☹', # ./images/smilies/icon_e_sad.gif
    ':|': '😐',
    ':-|': '😐', # ./images/smilies/icon_neutral.gif
    ':?': '😕',
    ':-?': '😕',
    '8-)': '😎',
    '8)': '😎',
    ':x': '😠', # ./images/smilies/icon_mad.gif
    ':-x': '😠', # ./images/smilies/icon_mad.gif
    ':P': '😛',
    ':-P': '😛 ', # ./images/smilies/icon_razz.gif
    ':o': '😮',
    ':cry:': '😢',
    ':roll:': '🙄',
    ':lol:': '😂',
    ':geek:': '🤓',
    ':ugeek:': '🤓',
    ':oops:': '😳',
    ':evil:': '👿',
    ':shock:': '😲',
    ':twisted:': '😈', # ./images/smilies/icon_twisted.gif
    ':!:': '⚠️',
    ':?:': '🤔',
    ':mrgreen:': '🔰',
    ':idea:': '💡',
    ':arrow:': '➡️', # ./images/smilies/icon_arrow.gif
}

TOPIC_ID = re.compile(r"t=(\d+?)&")

DEFAULT_CACHE_DIR = '.cache'
DEFAULT_CACHE_AGE = 60 * 60 # 1 hour

if settings:
    DEFAULT_CACHE_DIR = os.path.join(settings.PROJECT_PATH, 'data', 'phpbb_cache')
    DEFAULT_CACHE_AGE = getattr(settings, 'HTTP_SYNC_CACHE_AGE', DEFAULT_CACHE_AGE)


def get_size(num, unit):
    """Save a size number always as KiB"""
    num = num.strip().strip('(')
    return float(num) * {
        'Bytes': 1 / 1024,
        'KiB': 1,
        'MiB': 1024,
        'GiB': 1014 * 1024,
    }[unit]

def get_generator(gen, fname):
    """Yield items from a generator and save the results"""
    data = []
    for item in gen:
        data.append(item)
        yield item
    with open(fname, 'w') as fhl:
        fhl.write(json.dumps(data))

class ResourceBase(object):
    """A base class for resource methods, turns pages into json"""
    def __init__(self, resource_id, parent=None, **data):
        if parent is not None:
            data['cache_age'] = parent.cache_age
            data['cache_dir'] = parent.cache_dir

        self.cache_age = data.pop('cache_age', DEFAULT_CACHE_AGE)
        self.cache_dir = data.pop('cache_dir', DEFAULT_CACHE_DIR)

        self.parent = parent
        self.resource_id = resource_id
        self.data = data

        if not os.path.isdir(self.cache_dir):
            os.makedirs(self.cache_dir)

    @property
    def key(self):
        """The key name helps distinguish this from others"""
        raise NotImplementedError("Key must be defined to download resource.")

    def method(self):
        """The method does the heavy lifting of downloading"""
        raise NotImplementedError("Key must have a method to download data.")

    def get(self, *args):
        """Get a resource and save the output to json (cached)"""
        cache_filename = os.path.join(self.cache_dir, self.key + '.json')
        if os.path.exists(cache_filename):
            try:
                with open(cache_filename, 'r') as fhl:
                    return json.loads(fhl.read())
            except json.decoder.JSONDecodeError:
                os.unlink(cache_filename)

        if '/' in cache_filename:
            dirname = os.path.dirname(cache_filename)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)

        data = self.method(*args)
        if isinstance(data, types.GeneratorType):
            return get_generator(data, cache_filename)
        with open(cache_filename, 'w') as fhl:
            fhl.write(json.dumps(data))

        return data

    def get_http(self, url, reffer=None, key=None, binary=False):
        """Makes a http request and returns the content, caches it in CACHE_DIR"""
        url = urljoin(reffer or '', url)

        if '://' not in url:
            raise IOError("URL generation failed: %s reffer=%s" % (url, reffer))

        if not key:
            key = hashlib.sha224(url.encode("utf-8")).hexdigest() + '.html'

        cache_filename = os.path.join(self.cache_dir, 'http', key)

        if os.path.isfile(cache_filename):
            if binary:
                return cache_filename

            age = time.time() - os.stat(cache_filename)[stat.ST_MTIME]
            if age < self.cache_age:
                with open(cache_filename, 'r') as fhl:
                    return (url, fhl.read())

        try:
            req = Request(url)
            req.add_header('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de;'
                           'rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5')
            logging.debug("GETTING: %s", url)
            content = urlopen(req).read()
        except Exception as err:
            logging.error("url: '%s' not working: %s", url, str(err))
            return (url, '')

        fdir = os.path.dirname(cache_filename)
        if not os.path.isdir(fdir):
            os.makedirs(fdir)

        with open(cache_filename, 'wb') as fhl:
            fhl.write(content)

        if binary:
            return cache_filename

        return (url, content)

    def get_html(self, url, reffer=None):
        """Returns a Http request wrapped in soup"""
        (url, content) = self.get_http(url, reffer)
        return (url, BeautifulSoup(content, "html5lib"))

    def get_pages(self, url, reffer=None):
        """Get the next page, based on the start page"""
        (prev_url, next_url) = (reffer, url)
        while next_url:
            (prev_url, page) = self.get_html(next_url, reffer=prev_url)
            anchor = page.findAll('a', {'rel': 'next'})
            next_url = anchor[0].get('href') if anchor else None
            yield (prev_url, page)

    def __iter__(self):
        """Generate child objects from the resource_id."""
        for (resource_id, data) in self.get().items():
            yield self.child_class(resource_id=resource_id, parent=self, **data)


class BeeBeePost(ResourceBase):
    """A single post in a comment thread"""
    pass


class BeeBeeThread(ResourceBase):
    """A single phpBB thread on a phphBB site."""
    key = property(lambda self: 'thread/' + self.thread_id)
    forum = property(lambda self: self.parent)
    reffer = property(lambda self: self.forum.site.site_url)
    child_class = BeeBeePost

    def method(self):
        """From a single page with post, extract the posts structured """
        names = OrderedDict()
        for page_url, page in self.get_pages(self.data['link'], reffer=self.reffer):
            for post in page.find_all("div", "postbody"):
                try:
                    author = post.find_all("p", 'author')[0].find_all('a')[1].get_text()
                except Exception as err:
                    author = post.find_all("span", 'username')[0].get_text()

                text = re.sub(r'[^\w\s:]', "", post.find("p", "author").get_text())
                content = post.find("div", "content")
                self.replace_emoji(content.find_all("img", "smilies"))
                self.replace_emoji(content.find_all("img", "smiley"))
                self.replace_links(page_url, content.find_all('a', 'postlink-local'))
                self.replace_links(page_url, content.find_all('a', 'postlink'))

                comment_id = post.find("h3").find("a").get("href").strip("#")
                names[comment_id] = {
                    "date": text.split(author)[-1].strip(),
                    "content": str(content)[21:-6], # Cut out content div
                    "author": author,
                }

                #files = post.find_all('dl', 'file')
                #if files:
                #    ret["files"] = list(self.get_files(files, page_url))

                #links = content.find_all('a', 'postlink')
                #if links:
                #    ret["links"] = [l.get('href') for l in links]

                #images = content.find_all('img', 'postimage')
                #if images:
                #    ret["images"] = list(self.get_images(images, page_url))

        return names

    @staticmethod
    def replace_emoji(smilies):
        """Convert forum smilies into utf-8 emojis"""
        for smilie in smilies:
            sid = smilie.get('alt')
            if sid in EMOJI:
                smilie.replaceWith(EMOJI[sid])
            elif sid[0] == ':' and sid[-1] == ':':
                smilie.replaceWith(sid)
            else:
                name = smilie.get('src')
                logging.error("  '%s': '', # %s SMILIE", sid, name)

    def replace_links(self, from_link, links):
        """Take links to local pages and replace them"""
        from_url = urlparse(from_link)
        for link in links:
            url = urlparse(link.get('href'))
            qstr = parse_qs(url.query)
            if url.netloc == from_url.netloc: #'www.inkscapeforum.com':
                if url.fragment.startswith('p'):
                    link.replaceWith(':post%s:' % url.fragment)
                elif 'viewtopic.php' in url.path or 'posting.php' in url.path:
                    if 't' in qstr:
                        link.replaceWith(':topic%s:' % qstr['t'][0])
                    elif 'p' in qstr:
                        link.replaceWith(':post%s:' % qstr['p'][0])
                elif 'viewforum.php' in url.path:
                    link.replaceWith(':forum%s:' % qstr['f'][0])
                elif 'memberlist.php' in url.path:
                    link.replaceWith(':user%s:' % qstr['u'][0])
                elif 'search.php' in url.path:
                    if 'keywords' in qstr:
                        link.replaceWith(':search%s:' % qstr['keywords'][0])
                    else:
                        link.replaceWith(':search:')
                elif '/download/file.php' in url.path:
                    link.replaceWith(':download%s:' % qstr['id'][0])
                elif 'rss' in url.path:
                    pass
                else:
                    logging.error("Unknown link: %s", str(url))

    def get_files(self, files, reffer):
        """Get the linked files and save them"""
        for dl_file in files:
            (size, views) = dl_file.find_all('dd')[-1].get_text().split(') ')
            anchor = dl_file.find('a', 'postlink')
            img = dl_file.find('img', 'postimage')

            if anchor:
                link = anchor.get('href')
                fname = 'attachment/' + anchor.get_text()
            elif img:
                (fname, size) = size.rsplit(' (', 1)
                link = img.get('src')
                fname = 'image/' + fname
            else:
                raise IOError("Can't find file in %s" % str(anchor))

            yield {
                'id': re.compile(r"id=(\d+?)&").findall(link)[0],
                'size': get_size(*size.split(' ')),
                'views': int(views.split(' ')[1]),
                'filename': self.get_file(link, reffer, fname),
            }

    def get_images(self, images, reffer):
        """Get a list of images in the document"""
        for x, img in enumerate(images):
            yield self.get_file(img.get('src'), reffer, 'image/' + img.get('src').split('/')[-1])
            img.replaceWith(':img%d:' % x)

    def get_file(self, url, reffer, filename):
        """Downloads a file and saves it for later"""
        return self.get_http(url, reffer, key=filename, binary=True)


class BeeBeeForum(ResourceBase):
    """A single phpBB forum on a phpBB site."""
    key = property(lambda self: 'forum/' + self.forum_id)
    site = property(lambda self: self.parent)
    child_class = BeeBeeThread

    def method(self):
        """Go through the topic pages of a forum and then gather all the topics
           via the step of gathering all the pages in the subforum """
        names = OrderedDict()
        url = self.data['link']
        reffer = self.site.site_url
        for (_, page) in self.get_pages(url, reffer=reffer):
            for anchor in page.find_all("a", "topictitle"):
                user = list(anchor.parent.find_all('div', 'responsive-hide')[0].children)
                views = anchor.parent.parent.parent.parent.find_all('dd', 'views')[0]
                link = anchor.get('href')
                tid = TOPIC_ID.findall(link)[0]
                names[tid] = {
                    'link': link,
                    'name': anchor.text,
                    'author': user[1].text,
                    'created': user[2][2:30].strip(),
                    'views': list(views.children)[0],
                }
        return names


class BeeBeeSite(ResourceBase):
    """A downloader of phpBB site content."""
    key = 'forums'
    child_class = BeeBeeForum
    site_url = property(lambda self: self.resource_id)

    def method(self):
        """Download the sub-forums"""
        names = OrderedDict()
        for href in self.get_html(self.site_url)[1].find_all("a", "forumtitle"):
            parent = href.parent.parent.parent.parent.parent.parent.\
                                 find_all('li', 'header')[0].find_all('a')[0]
            url = parent.get("href")
            parent_id = re.compile(r"f=(\d+?)&").findall(url)[0]
            names[parent_id] = {
                'link': parent.get("href"),
                'name': parent.text,
                'group': None,
                'desc': None,
            }

            url = href.get("href")
            desc = str(href.parent.contents[4]).strip()
            forum_id = re.compile(r"f=(\d+?)&").findall(url)[0]
            names[forum_id] = {'link': url, 'name': href.text, 'group': parent_id, 'desc': desc}
        return names
