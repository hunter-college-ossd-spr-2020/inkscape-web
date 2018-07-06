#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
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
These are important url debugging and iter tools (introspective)
"""

import types
import random
import logging

from string import ascii_uppercase, ascii_lowercase, digits

from django.conf.urls import url, include
from django.core.urlresolvers import reverse
from django.utils.text import slugify
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)

LOGGER = logging.getLogger('main')
LOGGER.setLevel(logging.INFO)

def url_tree(regex, *urls):
    """Provide a way to extend patterns easily"""
    class UrlTwig(object): # pylint: disable=too-few-public-methods, missing-docstring
        urlpatterns = urls
    return url(regex, include(UrlTwig))

class Url(object):
    """Load in a django URL and parse it for information"""
    is_module = False
    is_view = False

    def __init__(self, parent, entry, module):
        self.depth = 0
        self.parent = parent
        self.entry = entry
        self.pattern = entry.regex.pattern
        self.module = module

        if parent is not None:
            self.depth = parent.depth + 1

    def __str__(self):
        if self.name:
            return "%s [%s]" % (self.full_pattern, self.name)
        return self.full_pattern

    @property
    def name(self):
        """Returns the name of the url, plus namespace"""
        name = getattr(self.entry, 'name', None)
        namespace = self.namespace
        if name and namespace:
            return "%s:%s" % (namespace, name)
        elif name:
            return name
        return None

    @property
    def slug(self):
        """Returns the slugified pattern to identify this url"""
        name = self.name
        if name is None:
            return slugify(self.pattern)
        if self.kwargs:
            name += '?' + '+'.join(self.kwargs)
        return name

    @property
    def kwargs(self):
        """Gathers all kwargs from this and every parent regex"""
        kwargs = self.parent.kwargs if self.parent else {}
        kwargs.update(self.entry.regex.groupindex)
        return kwargs

    @property
    def full_pattern(self):
        """Returns the fullregular expression for this url"""
        pattern = self.pattern.lstrip('^').rstrip('$')
        if self.parent:
            if pattern and self.parent.pattern.endswith('$'):
                LOGGER.warning("Possible broken url, parent url ends "
                               "string matching: %s", self.parent)
            pattern = self.parent.full_pattern + pattern
        if pattern == 'None/':
            return '/'
        return pattern

    @property
    def namespace(self):
        """Returns the namespace if it's defined"""
        if hasattr(self.entry, 'namespace') and self.entry.namespace:
            return self.entry.namespace
        if self.parent is not None:
            return self.parent.namespace
        return None

    def test_url(self, *args, **kw):
        """Atttempt to generate a test url based on these kwargs"""
        if self.name:
            return reverse(self.name, args=args, kwargs=kw)
        if not self.kwargs:
            # Construct the pattern without any
            return '/' + self.full_pattern.lstrip('^').rstrip('$')
        return None

    def test_404_urls(self, *args, **kw):
        """Attempt to generate a test url, but replace kwargs to generate a 404"""
        if args and kw:
            raise KeyError("You can not use args and kwargs in urls at the same time.")
        if args:
            args = list(args)
            for x, arg in enumerate(args):
                # Randomly replace one argument in the args each time
                rep = [random_change(arg)]
                yield self.test_url(*(args[:x] + rep + args[x+1:]))
        elif kw:
            for key, arg in kw.items():
                r_kw = kw.copy()
                r_kw[key] = random_change(arg, key=key)
                yield self.test_url(*args, **r_kw)


def random_change(data, key=None):
    """Change the variable into a random variation (slug or pk usually)"""
    if key == 'year':
        return random.randint(int(data) + 10, int(data) + 100)
    if key in ['month', 'day']:
        return '00'
    if isinstance(data, str) and data.isdigit():
        data = int(data)
    if isinstance(data, int):
        return random.randint((data+10) * 10, (data+10) * 100)
    chars = ascii_uppercase + ascii_lowercase + digits + '_-'
    if data == data.lower():
        chars = chars[26:]
    return ''.join(random.choice(chars) for _ in range(len(data)))


class UrlModule(Url):
    """A url include"""
    is_module = True

    def __str__(self):
        if self.name == 'UrlTwig':
            return "{} ^>".format(self.full_pattern)
        return "%s > %s >>" % (self.full_pattern, self.name)

    @property
    def name(self):
        return self.urls_name(self.module)

    def urls_name(self, urlc):
        """Returns the urls own name"""
        if isinstance(urlc, list) and urlc:
            return self.urls_name(urlc[0])
        elif hasattr(urlc, '__name__'):
            return urlc.__name__
        return None

class UrlFunction(Url):
    """A url using a simple function"""
    def __str__(self):
        tag = super(UrlFunction, self).__str__()
        return "%s > %s()" % (tag, self.module.__name__)

class UrlView(Url):
    """A url using a generic class based view"""
    is_view = True

    def __str__(self):
        tag = super(UrlView, self).__str__()
        return "%s > %s %s.%s" % (tag, self.url_type_name, self.app, self.model.__name__)

    URL_UNKNOWN_TYPE = 0
    URL_LIST_TYPE = 1
    URL_DETAIL_TYPE = 2
    URL_CREATE_TYPE = 3
    URL_UPDATE_TYPE = 4
    URL_DELETE_TYPE = 5

    VIEW_NAMES = ['Unknown', 'List', 'Detail', 'Create', 'Update', 'Delete']
    VIEW_CLASSES = [None, ListView, DetailView, CreateView, UpdateView, DeleteView]

    @classmethod
    def get_url_type(cls, view):
        """Returns the urls type index, if it'sa known type"""
        for index, view_cls in enumerate(cls.VIEW_CLASSES):
            if view_cls is not None and isinstance(view, view_cls):
                return index
        return 0

    @property
    def url_type(self):
        """Returns the url_type for this module"""
        return self.get_url_type(self.module)

    @property
    def url_type_name(self):
        """Returns the url type name, such as List or Detail"""
        return self.VIEW_NAMES[self.url_type]

    @property
    def app(self):
        """Attemptsto find the app name for this module"""
        return self.module.__module__.split('.views')[0]

    @property
    def model(self):
        """Returns the model involved in this view"""
        if hasattr(self.module, 'model'):
            # self.module is the View class
            return self.module.model
        return type(None)


class WebsiteUrls(object):
    """A class that can loop through urls in a tree structure"""
    def __iter__(self):
        """
        Yields every url with a Url class, see Url() for details.
        """
        dupes = {}
        import inkscape.urls
        for item in self.url_iter(inkscape.urls.urlpatterns):
            key = (item.name, item.full_pattern)
            if not item.is_module:
                if key is not None and key in dupes:
                    LOGGER.error(
                        "URL Name is already used '%s' -> '%s'\n a) %s\n b) %s",
                        key[0], key[1], str(dupes[key]), str(item))
                dupes[key] = item
            yield item

    def url_iter(self, urllist, parent=None):
        """
        Returns a specific arm of the urls tree (see __iter__)
        """
        for entry in urllist:
            if hasattr(entry, 'url_patterns'):
                if hasattr(entry, 'urlconf_name'):
                    this_parent = UrlModule(parent, entry, entry.urlconf_name)
                    if this_parent.name:
                        yield this_parent

                    # replace with yield from (python 3.3) when possible.
                    for item in self.url_iter(entry.url_patterns, this_parent):
                        yield item
                continue

            if hasattr(entry, 'callback'):
                callback = entry.callback
                if isinstance(callback, types.FunctionType):
                    yield UrlFunction(parent, entry, callback)
                elif hasattr(callback, 'model') and callback.model is not None:
                    yield UrlView(parent, entry, callback)
                else:
                    yield Url(parent, entry, callback)
